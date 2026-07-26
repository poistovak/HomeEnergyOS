from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from heos.policy.mode_policy import ModePolicy
from heos.policy.release_mode_bridge import ReleaseModeBridge
from heos.release_gate import (
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleasePolicy,
    ReleaseStatus,
    mode_rank,
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
    candidate_id: str = "candidate:authority"
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
    decision_id: str = "authority-decision-1"
    generated_at: datetime = NOW - timedelta(minutes=1)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


def request(mode: OperationMode) -> OperationalRequest:
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
        operator_approved=True,
        autonomy_authorized=True,
    )


@pytest.mark.parametrize(
    ("bridge_maximum", "release_maximum"),
    [
        (OperationMode.AUTONOMOUS, OperationMode.OBSERVE),
        (OperationMode.AUTONOMOUS, OperationMode.ADVISE),
        (OperationMode.AUTONOMOUS, OperationMode.SUPERVISED),
        (OperationMode.SUPERVISED, OperationMode.OBSERVE),
        (OperationMode.SUPERVISED, OperationMode.ADVISE),
        (OperationMode.ADVISE, OperationMode.OBSERVE),
    ],
)
def test_release_gate_rejects_mode_above_its_authority(
    bridge_maximum,
    release_maximum,
):
    effective, _ = ReleaseModeBridge(
        ModePolicy(maximum_mode=bridge_maximum)
    ).apply(
        request(OperationMode.AUTONOMOUS)
    )

    assert mode_rank(effective.requested_mode) > mode_rank(
        release_maximum
    )

    decision = OperationalReleaseGate(
        ReleasePolicy(
            maximum_mode=release_maximum,
        )
    ).review(effective)

    assert decision.status is ReleaseStatus.REJECTED
    assert decision.intent is None


@pytest.mark.parametrize(
    "maximum",
    [
        OperationMode.OBSERVE,
        OperationMode.ADVISE,
        OperationMode.SUPERVISED,
        OperationMode.AUTONOMOUS,
    ],
)
def test_matching_policy_authority_releases_effective_mode(
    maximum,
):
    effective, result = ReleaseModeBridge(
        ModePolicy(maximum_mode=maximum)
    ).apply(
        request(OperationMode.AUTONOMOUS)
    )

    decision = OperationalReleaseGate(
        ReleasePolicy(
            maximum_mode=maximum,
        )
    ).review(effective)

    assert result.effective_mode is maximum
    assert decision.status is ReleaseStatus.RELEASED
    assert decision.intent is not None
    assert decision.intent.requested_mode is maximum