from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from heos.compiler import DecisionCompiler
from heos.compiler.intent_bridge import IntentCompilerBridge
from heos.execution import (
    ExecutionResult,
    ExecutionRuntime,
    ExecutionStatus,
)
from heos.execution.safety_gate import SafetyExecutionGate
from heos.kernel import (
    EnergyBalance,
    KernelHealth,
    KernelSnapshot,
)
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleasePolicy,
    ReleaseStatus,
    standard_manifest,
)
from heos.result_verification.autonomy_admission import (
    AutonomyAdmissionGate,
    AutonomyAdmissionStatus,
)
from heos.result_verification.decision_confidence_gate import (
    DecisionConfidenceGate,
)
from heos.result_verification.reasoning_orchestrator import (
    ReasoningResult,
)
from heos.safety import (
    SafetyContext,
    SafetyEngine,
    SafetyVerdict,
)

NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class FakeControl:
    battery_power_kw: float = 0.0
    ev_charge_kw: float = 2.0
    hvac_thermal_kw: float = 0.0


@dataclass(frozen=True, slots=True)
class FakeCandidate:
    candidate_id: str = "candidate:balanced"
    controls: tuple[FakeControl, ...] = (FakeControl(),)
    objective: str = "balanced"


@dataclass(frozen=True, slots=True)
class FakeMetrics:
    objective_score: float = 1.25
    violation_count: int = 0
    violation_magnitude: float = 0.0


@dataclass(frozen=True, slots=True)
class FakeEvaluation:
    candidate: FakeCandidate = FakeCandidate()
    metrics: FakeMetrics = FakeMetrics()
    feasible: bool = True
    rank: int = 1


@dataclass(frozen=True, slots=True)
class FakeDecision:
    decision_id: str = "strategy-decision-vertical-1"
    generated_at: datetime = NOW - timedelta(minutes=2)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


class CountingDriver:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, step):
        self.calls += 1
        return ExecutionResult(
            success=True,
            message=f"Executed: {step.description}",
        )


def manifest():
    return standard_manifest(
        NOW,
        forecast="forecast-1",
        feedback="feedback-1",
        memory="memory-1",
        digital_twin="digital-twin-1",
        calibration="calibration-1",
        strategy="strategy-1",
        compiler="compiler-1",
        safety="safety-1",
        execution="execution-1",
    )


def request(
    *,
    autonomy_authorized: bool,
) -> OperationalRequest:
    return OperationalRequest(
        strategy_decision=FakeDecision(),
        requested_mode=OperationMode.AUTONOMOUS,
        evaluated_at=NOW,
        manifest=manifest(),
        readiness=ReadinessEvidence(),
        operator_approved=True,
        autonomy_authorized=autonomy_authorized,
        metadata=(("site", "vertical-test"),),
    )


def kernel(
    health: KernelHealth = KernelHealth.READY,
) -> KernelSnapshot:
    return KernelSnapshot(
        health=health,
        balance=EnergyBalance(
            production_w=6000.0,
            consumption_w=3000.0,
            storage_charge_w=0.0,
            storage_discharge_w=0.0,
            grid_import_w=2000.0,
            grid_export_w=0.0,
        ),
        resource_count=4,
        flow_count=3,
    )


def admission_gate() -> AutonomyAdmissionGate:
    return AutonomyAdmissionGate(
        confidence_gate=DecisionConfidenceGate(
            minimum_confidence=0.6,
        )
    )


def release_gate() -> OperationalReleaseGate:
    return OperationalReleaseGate(
        ReleasePolicy(
            maximum_mode=OperationMode.AUTONOMOUS,
        )
    )


def test_low_confidence_stops_before_operational_release():
    admission = admission_gate().evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=0.4,
        )
    )

    assert admission.status is AutonomyAdmissionStatus.ABSTAINED
    assert admission.admitted is False


def test_high_confidence_without_authorization_never_creates_intent():
    admission = admission_gate().evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=1.0,
        )
    )

    assert admission.admitted is True

    release = release_gate().review(
        request(
            autonomy_authorized=False,
        )
    )

    assert release.status is ReleaseStatus.HELD
    assert release.released is False
    assert release.intent is None


def test_authorized_safe_decision_reaches_execution_driver():
    admission = admission_gate().evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=1.0,
        )
    )

    assert admission.admitted is True

    release = release_gate().review(
        request(
            autonomy_authorized=True,
        )
    )

    assert release.status is ReleaseStatus.RELEASED
    assert release.intent is not None

    scenario = IntentCompilerBridge().scenario_id(
        release.intent
    )

    plan = DecisionCompiler().compile(
        scenario
    )

    driver = CountingDriver()

    execution = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    ).run(
        SafetyContext(
            plan=plan,
            kernel=kernel(),
            projected_grid_import_w=2000.0,
            maximum_grid_import_w=8000.0,
        )
    )

    assert execution.safety.verdict is SafetyVerdict.ALLOW
    assert execution.executed is True
    assert execution.runtime is not None
    assert execution.runtime.status is ExecutionStatus.COMPLETED
    assert driver.calls == len(plan.steps)
    assert driver.calls == 5


def test_authorized_decision_is_still_blocked_by_safety():
    admission = admission_gate().evaluate(
        ReasoningResult(
            decision="charge_battery",
            confidence=1.0,
        )
    )

    assert admission.admitted is True

    release = release_gate().review(
        request(
            autonomy_authorized=True,
        )
    )

    assert release.status is ReleaseStatus.RELEASED
    assert release.intent is not None

    scenario = IntentCompilerBridge().scenario_id(
        release.intent
    )

    plan = DecisionCompiler().compile(
        scenario
    )

    driver = CountingDriver()

    execution = SafetyExecutionGate(
        safety_engine=SafetyEngine(),
        runtime=ExecutionRuntime(driver),
    ).run(
        SafetyContext(
            plan=plan,
            kernel=kernel(),
            manual_lock=True,
            projected_grid_import_w=2000.0,
            maximum_grid_import_w=8000.0,
        )
    )

    assert execution.safety.verdict is SafetyVerdict.DENY
    assert execution.executed is False
    assert execution.runtime is None
    assert driver.calls == 0