from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from heos.coordination import (
    AutonomyController,
    CoordinationContext,
    CoordinationState,
)
from heos.coordination.coordinator import CoordinationCoordinator
from heos.policy.mode_policy import ModePolicy
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleasePolicy,
    ReleaseStatus,
    standard_manifest,
)

NOW = datetime(2026, 7, 26, 12, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class FakeControl:
    battery_power_kw: float = 0.0
    ev_charge_kw: float = 2.0
    hvac_thermal_kw: float = 0.0


@dataclass(frozen=True, slots=True)
class FakeCandidate:
    candidate_id: str = "candidate:coordination"
    controls: tuple[FakeControl, ...] = (FakeControl(),)
    objective: str = "balanced"


@dataclass(frozen=True, slots=True)
class FakeMetrics:
    objective_score: float = 1.0
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
    decision_id: str = "coordination-autonomy-decision"
    generated_at: datetime = NOW - timedelta(minutes=1)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


def make_request(
    mode: OperationMode,
    *,
    operator_approved: bool = False,
    autonomy_authorized: bool = False,
) -> OperationalRequest:
    return OperationalRequest(
        strategy_decision=FakeDecision(),
        requested_mode=mode,
        evaluated_at=NOW,
        manifest=standard_manifest(
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
        ),
        readiness=ReadinessEvidence(),
        operator_approved=operator_approved,
        autonomy_authorized=autonomy_authorized,
    )


def controller(
    *,
    mode_maximum: OperationMode,
    release_maximum: OperationMode = OperationMode.AUTONOMOUS,
) -> AutonomyController:
    return AutonomyController(
        mode_policy=ModePolicy(
            maximum_mode=mode_maximum,
        ),
        release_gate=OperationalReleaseGate(
            ReleasePolicy(
                maximum_mode=release_maximum,
            )
        ),
    )


def validating_context() -> CoordinationContext:
    return CoordinationContext(
        cycle_id="era4-autonomy-boundary",
        state=CoordinationState.VALIDATING.value,
    )


def test_released_request_enters_execution():
    context = validating_context()

    result = CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.ADVISE,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert result.release.status is ReleaseStatus.RELEASED
    assert context.state == CoordinationState.EXECUTING.value


def test_held_request_stays_in_validation():
    context = validating_context()

    result = CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.SUPERVISED,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert result.release.status is ReleaseStatus.HELD
    assert context.state == CoordinationState.VALIDATING.value


def test_rejected_request_fails_cycle():
    context = validating_context()

    result = CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.AUTONOMOUS,
            release_maximum=OperationMode.ADVISE,
        ),
        request=make_request(
            OperationMode.AUTONOMOUS,
            operator_approved=True,
            autonomy_authorized=True,
        ),
    )

    assert result.release.status is ReleaseStatus.REJECTED
    assert context.state == CoordinationState.FAILED.value


def test_authorization_requires_validating_state():
    context = CoordinationContext(
        cycle_id="wrong-state",
        state=CoordinationState.PLANNING.value,
    )

    with pytest.raises(
        ValueError,
        match="VALIDATING",
    ):
        CoordinationCoordinator().authorize_execution(
            context,
            controller=controller(
                mode_maximum=OperationMode.ADVISE,
            ),
            request=make_request(OperationMode.AUTONOMOUS),
        )


def test_coordination_records_requested_mode():
    context = validating_context()

    CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.ADVISE,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert context.metadata["autonomy_requested_mode"] == "autonomous"


def test_coordination_records_effective_mode():
    context = validating_context()

    CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.ADVISE,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert context.metadata["autonomy_effective_mode"] == "advise"


def test_coordination_records_downgrade():
    context = validating_context()

    CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.ADVISE,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert context.metadata["autonomy_downgraded"] is True


def test_coordination_records_release_status_and_id():
    context = validating_context()

    result = CoordinationCoordinator().authorize_execution(
        context,
        controller=controller(
            mode_maximum=OperationMode.ADVISE,
        ),
        request=make_request(OperationMode.AUTONOMOUS),
    )

    assert context.metadata["release_status"] == "released"
    assert context.metadata["release_id"] == result.release.release_id