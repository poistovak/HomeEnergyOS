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
    candidate_id: str = "candidate:approval-resume"
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
    decision_id: str = "approval-resume-decision"
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
    maximum: OperationMode,
) -> AutonomyController:
    return AutonomyController(
        mode_policy=ModePolicy(
            maximum_mode=maximum,
        ),
        release_gate=OperationalReleaseGate(
            ReleasePolicy(
                maximum_mode=OperationMode.AUTONOMOUS,
            )
        ),
    )


def validating_context() -> CoordinationContext:
    return CoordinationContext(
        cycle_id="era4-approval-resume",
        state=CoordinationState.VALIDATING.value,
    )


def test_supervised_held_then_operator_approval_releases():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
    )
    coordinator = CoordinationCoordinator()
    autonomy = controller(OperationMode.SUPERVISED)

    first = coordinator.authorize_execution(
        context,
        controller=autonomy,
        request=original,
    )

    assert first.release.status is ReleaseStatus.HELD
    assert context.state == CoordinationState.VALIDATING.value

    resumed = coordinator.resume_with_approval(
        context,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    assert resumed.release.status is ReleaseStatus.RELEASED
    assert context.state == CoordinationState.EXECUTING.value


def test_autonomous_operator_approval_alone_stays_held():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
    )
    coordinator = CoordinationCoordinator()
    autonomy = controller(OperationMode.AUTONOMOUS)

    coordinator.authorize_execution(
        context,
        controller=autonomy,
        request=original,
    )

    resumed = coordinator.resume_with_approval(
        context,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    assert resumed.release.status is ReleaseStatus.HELD
    assert context.state == CoordinationState.VALIDATING.value


def test_autonomous_full_approval_releases():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
    )
    coordinator = CoordinationCoordinator()
    autonomy = controller(OperationMode.AUTONOMOUS)

    coordinator.authorize_execution(
        context,
        controller=autonomy,
        request=original,
    )

    resumed = coordinator.resume_with_approval(
        context,
        controller=autonomy,
        request=original,
        operator_approved=True,
        autonomy_authorized=True,
    )

    assert resumed.release.status is ReleaseStatus.RELEASED
    assert context.state == CoordinationState.EXECUTING.value


def test_resume_requires_validating_state():
    context = CoordinationContext(
        cycle_id="invalid-resume-state",
        state=CoordinationState.EXECUTING.value,
    )

    with pytest.raises(
        ValueError,
        match="VALIDATING",
    ):
        CoordinationCoordinator().resume_with_approval(
            context,
            controller=controller(OperationMode.SUPERVISED),
            request=make_request(OperationMode.AUTONOMOUS),
            operator_approved=True,
        )


def test_resume_does_not_mutate_original_request():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
    )

    CoordinationCoordinator().resume_with_approval(
        context,
        controller=controller(OperationMode.SUPERVISED),
        request=original,
        operator_approved=True,
    )

    assert original.operator_approved is False
    assert original.autonomy_authorized is False


def test_resume_preserves_existing_operator_approval_when_unspecified():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
        operator_approved=True,
    )

    resumed = CoordinationCoordinator().resume_with_approval(
        context,
        controller=controller(OperationMode.AUTONOMOUS),
        request=original,
        autonomy_authorized=True,
    )

    assert resumed.release.status is ReleaseStatus.RELEASED


def test_resume_preserves_existing_autonomy_authorization_when_unspecified():
    context = validating_context()
    original = make_request(
        OperationMode.AUTONOMOUS,
        autonomy_authorized=True,
    )

    resumed = CoordinationCoordinator().resume_with_approval(
        context,
        controller=controller(OperationMode.AUTONOMOUS),
        request=original,
        operator_approved=True,
    )

    assert resumed.release.status is ReleaseStatus.RELEASED


def test_resume_is_audited_in_coordination_metadata():
    context = validating_context()

    CoordinationCoordinator().resume_with_approval(
        context,
        controller=controller(OperationMode.SUPERVISED),
        request=make_request(OperationMode.AUTONOMOUS),
        operator_approved=True,
    )

    assert context.metadata["approval_resume"] is True
    assert context.metadata["release_status"] == "released"