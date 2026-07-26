from datetime import UTC, datetime, timedelta

from heos.compiler import DecisionCompiler
from heos.compiler.intent_bridge import IntentCompilerBridge
from heos.release_gate import ExecutionIntent, OperationMode


def make_intent(
    *,
    ev_charge_kw: float,
) -> ExecutionIntent:
    now = datetime.now(UTC)

    return ExecutionIntent(
        intent_id="intent-001",
        source_decision_id="decision-001",
        candidate_id="candidate-001",
        requested_mode=OperationMode.AUTONOMOUS,
        created_at=now,
        not_after=now + timedelta(minutes=5),
        compiler_target="heos.decision_compiler",
        control_payload=(
            ("ev_charge_kw", ev_charge_kw),
        ),
    )


def test_released_ev_intent_compiles_to_charge_plan():
    intent = make_intent(
        ev_charge_kw=3.6,
    )

    scenario = IntentCompilerBridge().scenario_id(
        intent
    )

    plan = DecisionCompiler().compile(
        scenario
    )

    assert plan.scenario_id == "charge_ev_now"
    assert len(plan.steps) == 5
    assert plan.steps[0].description == "Kernel READY"


def test_observe_intent_compiles_to_safe_noop_plan():
    intent = make_intent(
        ev_charge_kw=0.0,
    )

    scenario = IntentCompilerBridge().scenario_id(
        intent
    )

    plan = DecisionCompiler().compile(
        scenario
    )

    assert plan.scenario_id == "observe_only"
    assert len(plan.steps) == 1
    assert plan.steps[0].description == "No-op verification"