from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from heos.coordination import (
    AutonomyController,
    CoordinationAuditTrail,
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
    candidate_id: str = "candidate:audit-trail"
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
    decision_id: str = "audit-trail-decision"
    generated_at: datetime = NOW - timedelta(minutes=1)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


def make_request(
    *,
    operator_approved: bool = False,
    autonomy_authorized: bool = False,
) -> OperationalRequest:
    return OperationalRequest(
        strategy_decision=FakeDecision(),
        requested_mode=OperationMode.AUTONOMOUS,
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


def context(
    cycle_id: str = "era4-audit",
) -> CoordinationContext:
    return CoordinationContext(
        cycle_id=cycle_id,
        state=CoordinationState.VALIDATING.value,
    )


def test_authorization_appends_audit_record():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )

    result = coordinator.authorize_execution(
        context(),
        controller=controller(OperationMode.ADVISE),
        request=make_request(),
    )

    records = trail.records()

    assert len(records) == 1
    assert records[0].release_id == result.release.release_id


def test_audit_records_requested_and_effective_modes():
    trail = CoordinationAuditTrail()

    CoordinationCoordinator(
        audit_trail=trail,
    ).authorize_execution(
        context(),
        controller=controller(OperationMode.ADVISE),
        request=make_request(),
    )

    record = trail.records()[0]

    assert record.requested_mode == "autonomous"
    assert record.effective_mode == "advise"
    assert record.downgraded is True


def test_audit_records_release_status():
    trail = CoordinationAuditTrail()

    CoordinationCoordinator(
        audit_trail=trail,
    ).authorize_execution(
        context(),
        controller=controller(OperationMode.SUPERVISED),
        request=make_request(),
    )

    record = trail.records()[0]

    assert record.release_status == ReleaseStatus.HELD.value


def test_first_held_record_is_not_resume():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )
    cycle = context()

    coordinator.authorize_execution(
        cycle,
        controller=controller(OperationMode.SUPERVISED),
        request=make_request(),
    )

    assert trail.records()[0].approval_resume is False


def test_resume_appends_second_record():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )
    cycle = context()
    original = make_request()
    autonomy = controller(OperationMode.SUPERVISED)

    coordinator.authorize_execution(
        cycle,
        controller=autonomy,
        request=original,
    )

    coordinator.resume_with_approval(
        cycle,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    assert len(trail.records()) == 2


def test_held_then_released_history_is_preserved():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )
    cycle = context()
    original = make_request()
    autonomy = controller(OperationMode.SUPERVISED)

    coordinator.authorize_execution(
        cycle,
        controller=autonomy,
        request=original,
    )

    coordinator.resume_with_approval(
        cycle,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    records = trail.records()

    assert records[0].release_status == "held"
    assert records[1].release_status == "released"


def test_resume_record_marks_approval_resume():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )
    cycle = context()
    original = make_request()
    autonomy = controller(OperationMode.SUPERVISED)

    coordinator.authorize_execution(
        cycle,
        controller=autonomy,
        request=original,
    )

    coordinator.resume_with_approval(
        cycle,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    assert trail.records()[1].approval_resume is True


def test_resume_record_captures_updated_approval_state():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )
    cycle = context()
    original = make_request()
    autonomy = controller(OperationMode.SUPERVISED)

    coordinator.authorize_execution(
        cycle,
        controller=autonomy,
        request=original,
    )

    coordinator.resume_with_approval(
        cycle,
        controller=autonomy,
        request=original,
        operator_approved=True,
    )

    records = trail.records()

    assert records[0].operator_approved is False
    assert records[1].operator_approved is True


def test_for_cycle_filters_records():
    trail = CoordinationAuditTrail()
    coordinator = CoordinationCoordinator(
        audit_trail=trail,
    )

    coordinator.authorize_execution(
        context("cycle-a"),
        controller=controller(OperationMode.ADVISE),
        request=make_request(),
    )

    coordinator.authorize_execution(
        context("cycle-b"),
        controller=controller(OperationMode.ADVISE),
        request=make_request(),
    )

    records = trail.for_cycle("cycle-a")

    assert len(records) == 1
    assert records[0].cycle_id == "cycle-a"


def test_records_returns_immutable_snapshot():
    trail = CoordinationAuditTrail()

    CoordinationCoordinator(
        audit_trail=trail,
    ).authorize_execution(
        context(),
        controller=controller(OperationMode.ADVISE),
        request=make_request(),
    )

    records = trail.records()

    assert isinstance(records, tuple)
    assert len(records) == 1