from datetime import UTC, datetime, timedelta

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


def test_positive_ev_charge_maps_to_charge_scenario():
    bridge = IntentCompilerBridge()

    scenario = bridge.scenario_id(
        make_intent(
            ev_charge_kw=3.6,
        )
    )

    assert scenario == "charge_ev_now"


def test_zero_ev_charge_maps_to_observe_only():
    bridge = IntentCompilerBridge()

    scenario = bridge.scenario_id(
        make_intent(
            ev_charge_kw=0.0,
        )
    )

    assert scenario == "observe_only"


def test_negative_ev_charge_maps_to_observe_only():
    bridge = IntentCompilerBridge()

    scenario = bridge.scenario_id(
        make_intent(
            ev_charge_kw=-1.0,
        )
    )

    assert scenario == "observe_only"