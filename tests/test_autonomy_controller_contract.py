from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from heos.coordination import AutonomyController
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
    candidate_id: str = "candidate:autonomy-control"
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
    decision_id: str = "autonomy-control-decision"
    generated_at: datetime = NOW - timedelta(minutes=1)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


def request(
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


def test_controller_preserves_original_request():
    original = request(
        OperationMode.AUTONOMOUS,
    )

    result = controller(
        mode_maximum=OperationMode.ADVISE,
    ).evaluate(original)

    assert result.original_request is original
    assert original.requested_mode is OperationMode.AUTONOMOUS
    assert result.effective_request is not original


def test_controller_reports_downgrade():
    result = controller(
        mode_maximum=OperationMode.ADVISE,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert result.downgraded is True
    assert result.mode_result.requested_mode is OperationMode.AUTONOMOUS
    assert result.mode_result.effective_mode is OperationMode.ADVISE


def test_controller_releases_downgraded_advise_mode():
    result = controller(
        mode_maximum=OperationMode.ADVISE,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert result.release.status is ReleaseStatus.RELEASED
    assert result.released is True
    assert result.release.intent is not None
    assert result.release.intent.requested_mode is OperationMode.ADVISE


def test_controller_holds_supervised_without_operator_approval():
    result = controller(
        mode_maximum=OperationMode.SUPERVISED,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert result.mode_result.effective_mode is OperationMode.SUPERVISED
    assert result.release.status is ReleaseStatus.HELD
    assert result.released is False


def test_controller_releases_supervised_with_operator_approval():
    result = controller(
        mode_maximum=OperationMode.SUPERVISED,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
            operator_approved=True,
        )
    )

    assert result.release.status is ReleaseStatus.RELEASED
    assert result.released is True


def test_controller_holds_autonomous_without_authorization():
    result = controller(
        mode_maximum=OperationMode.AUTONOMOUS,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
            operator_approved=True,
            autonomy_authorized=False,
        )
    )

    assert result.downgraded is False
    assert result.release.status is ReleaseStatus.HELD


def test_controller_releases_fully_authorized_autonomous_mode():
    result = controller(
        mode_maximum=OperationMode.AUTONOMOUS,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
            operator_approved=True,
            autonomy_authorized=True,
        )
    )

    assert result.release.status is ReleaseStatus.RELEASED
    assert result.released is True
    assert result.release.intent is not None
    assert result.release.intent.requested_mode is OperationMode.AUTONOMOUS


def test_release_gate_remains_final_authority():
    result = controller(
        mode_maximum=OperationMode.AUTONOMOUS,
        release_maximum=OperationMode.ADVISE,
    ).evaluate(
        request(
            OperationMode.AUTONOMOUS,
            operator_approved=True,
            autonomy_authorized=True,
        )
    )

    assert result.mode_result.effective_mode is OperationMode.AUTONOMOUS
    assert result.release.status is ReleaseStatus.REJECTED
    assert result.release.intent is None