from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from heos.policy.mode_policy import ModePolicy
from heos.policy.release_mode_bridge import ReleaseModeBridge
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleasePolicy,
    ReleaseStatus,
    standard_manifest,
)

NOW = datetime(
    2026,
    7,
    26,
    12,
    0,
    tzinfo=UTC,
)


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
    decision_id: str = "decision-001"
    generated_at: datetime = NOW - timedelta(minutes=2)
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


def release_gate() -> OperationalReleaseGate:
    return OperationalReleaseGate(
        ReleasePolicy(
            maximum_mode=OperationMode.AUTONOMOUS,
        )
    )


def test_bridge_preserves_allowed_mode():
    bridge = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.AUTONOMOUS,
        )
    )

    request, result = bridge.apply(
        make_request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert request.requested_mode is OperationMode.AUTONOMOUS
    assert result.downgraded is False


def test_bridge_downgrades_autonomous_to_advise():
    bridge = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    )

    request, result = bridge.apply(
        make_request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert request.requested_mode is OperationMode.ADVISE
    assert result.effective_mode is OperationMode.ADVISE
    assert result.downgraded is True


def test_bridge_downgrades_autonomous_to_supervised():
    bridge = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.SUPERVISED,
        )
    )

    request, result = bridge.apply(
        make_request(
            OperationMode.AUTONOMOUS,
        )
    )

    assert request.requested_mode is OperationMode.SUPERVISED
    assert result.downgraded is True


def test_bridge_does_not_mutate_original_request():
    original = make_request(
        OperationMode.AUTONOMOUS,
    )

    bridge = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    )

    effective, _ = bridge.apply(original)

    assert original.requested_mode is OperationMode.AUTONOMOUS
    assert effective.requested_mode is OperationMode.ADVISE
    assert effective is not original


def test_downgrade_to_advise_releases_without_approval():
    original = make_request(
        OperationMode.AUTONOMOUS,
    )

    effective, result = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    ).apply(original)

    release = release_gate().review(effective)

    assert result.downgraded is True
    assert effective.requested_mode is OperationMode.ADVISE
    assert release.status is ReleaseStatus.RELEASED
    assert release.intent is not None
    assert release.intent.requested_mode is OperationMode.ADVISE


def test_downgrade_to_supervised_requires_operator_approval():
    original = make_request(
        OperationMode.AUTONOMOUS,
        operator_approved=False,
        autonomy_authorized=False,
    )

    effective, result = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.SUPERVISED,
        )
    ).apply(original)

    release = release_gate().review(effective)

    assert result.downgraded is True
    assert effective.requested_mode is OperationMode.SUPERVISED
    assert release.status is ReleaseStatus.HELD
    assert release.intent is None


def test_downgrade_to_supervised_releases_with_operator_approval():
    original = make_request(
        OperationMode.AUTONOMOUS,
        operator_approved=True,
        autonomy_authorized=False,
    )

    effective, result = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.SUPERVISED,
        )
    ).apply(original)

    release = release_gate().review(effective)

    assert result.downgraded is True
    assert effective.requested_mode is OperationMode.SUPERVISED
    assert release.status is ReleaseStatus.RELEASED
    assert release.intent is not None
    assert release.intent.requested_mode is OperationMode.SUPERVISED


def test_autonomous_mode_requires_autonomy_authorization():
    original = make_request(
        OperationMode.AUTONOMOUS,
        operator_approved=True,
        autonomy_authorized=False,
    )

    effective, result = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.AUTONOMOUS,
        )
    ).apply(original)

    release = release_gate().review(effective)

    assert result.downgraded is False
    assert effective.requested_mode is OperationMode.AUTONOMOUS
    assert release.status is ReleaseStatus.HELD
    assert release.intent is None


def test_autonomous_mode_releases_with_full_authorization():
    original = make_request(
        OperationMode.AUTONOMOUS,
        operator_approved=True,
        autonomy_authorized=True,
    )

    effective, result = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.AUTONOMOUS,
        )
    ).apply(original)

    release = release_gate().review(effective)

    assert result.downgraded is False
    assert effective.requested_mode is OperationMode.AUTONOMOUS
    assert release.status is ReleaseStatus.RELEASED
    assert release.intent is not None
    assert release.intent.requested_mode is OperationMode.AUTONOMOUS

def test_bridge_records_mode_audit_metadata():
    original = make_request(
        OperationMode.AUTONOMOUS,
    )

    effective, _ = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    ).apply(original)

    metadata = dict(effective.metadata)

    assert metadata["requested_mode"] == "autonomous"
    assert metadata["effective_mode"] == "advise"
    assert metadata["mode_downgraded"] == "true"
    assert metadata["mode_policy_reason"] == (
        "autonomous exceeds maximum advise"
    )


def test_release_decision_preserves_mode_audit_metadata():
    effective, _ = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    ).apply(
        make_request(
            OperationMode.AUTONOMOUS,
        )
    )

    release = release_gate().review(effective)
    metadata = dict(release.metadata)

    assert metadata["requested_mode"] == "autonomous"
    assert metadata["effective_mode"] == "advise"
    assert metadata["mode_downgraded"] == "true"


def test_execution_intent_preserves_mode_audit_metadata():
    effective, _ = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    ).apply(
        make_request(
            OperationMode.AUTONOMOUS,
        )
    )

    release = release_gate().review(effective)

    assert release.intent is not None

    metadata = dict(release.intent.metadata)

    assert metadata["requested_mode"] == "autonomous"
    assert metadata["effective_mode"] == "advise"
    assert metadata["mode_downgraded"] == "true"


def test_bridge_preserves_existing_metadata():
    original = make_request(
        OperationMode.AUTONOMOUS,
    )

    original = replace(
        original,
        metadata=(
            ("site", "lab"),
            ("scenario", "sunny"),
        ),
    )

    effective, _ = ReleaseModeBridge(
        policy=ModePolicy(
            maximum_mode=OperationMode.ADVISE,
        )
    ).apply(original)

    metadata = dict(effective.metadata)

    assert metadata["site"] == "lab"
    assert metadata["scenario"] == "sunny"
    assert metadata["requested_mode"] == "autonomous"
    assert metadata["effective_mode"] == "advise"