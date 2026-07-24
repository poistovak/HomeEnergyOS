from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from math import inf, nan
from types import SimpleNamespace

import pytest

from heos.release_gate import (
    ComponentVersion,
    ExecutionIntent,
    GateCode,
    GateResult,
    InMemoryReleaseRepository,
    OperationalReleaseEngine,
    OperationalReleaseGate,
    OperationalRequest,
    OperationMode,
    ReadinessEvidence,
    ReleaseDecision,
    ReleasePolicy,
    ReleaseStatus,
    SystemManifest,
    control_payload,
    decision_shape_errors,
    dumps_release_decision,
    loads_release_decision,
    mode_rank,
    standard_manifest,
)

NOW = datetime(2026, 7, 15, 18, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class FakeControl:
    battery_power_kw: float = 0.0
    ev_charge_kw: float = 0.0
    hvac_thermal_kw: float = 0.0


@dataclass(frozen=True, slots=True)
class FakeCandidate:
    candidate_id: str = "candidate:balanced"
    controls: tuple[FakeControl, ...] = (FakeControl(1.0, 2.0, 3.0),)
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
    decision_id: str = "strategy-decision-1"
    generated_at: datetime = NOW - timedelta(minutes=2)
    selected: FakeEvaluation = FakeEvaluation()
    alternatives: tuple[FakeEvaluation, ...] = (FakeEvaluation(),)
    policy_version: str = "strategy-policy-1"
    parameter_version: str = "twin-parameters-1"


def manifest(**overrides: str) -> SystemManifest:
    values = {
        "forecast": "forecast-1",
        "feedback": "feedback-1",
        "memory": "memory-1",
        "digital_twin": "digital-twin-1",
        "calibration": "calibration-1",
        "strategy": "strategy-1",
        "compiler": "compiler-1",
        "safety": "safety-1",
        "execution": "execution-1",
    }
    values.update(overrides)
    return standard_manifest(NOW, **values)


def request(
    *,
    decision: object | None = None,
    mode: OperationMode = OperationMode.ADVISE,
    evaluated_at: datetime = NOW,
    system_manifest: SystemManifest | None = None,
    readiness: ReadinessEvidence | None = None,
    operator_approved: bool = False,
    autonomy_authorized: bool = False,
) -> OperationalRequest:
    return OperationalRequest(
        strategy_decision=decision or FakeDecision(),
        requested_mode=mode,
        evaluated_at=evaluated_at,
        manifest=system_manifest or manifest(),
        readiness=readiness or ReadinessEvidence(),
        operator_approved=operator_approved,
        autonomy_authorized=autonomy_authorized,
        metadata=(("site", "lab"),),
    )


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        (OperationMode.OBSERVE, 0),
        (OperationMode.ADVISE, 1),
        (OperationMode.SUPERVISED, 2),
        (OperationMode.AUTONOMOUS, 3),
    ],
)
def test_mode_rank(mode: OperationMode, expected: int) -> None:
    assert mode_rank(mode) == expected


@pytest.mark.parametrize(
    "missing",
    [
        "forecast",
        "feedback",
        "memory",
        "digital_twin",
        "calibration",
        "strategy",
        "compiler",
        "safety",
        "execution",
    ],
)
def test_manifest_reports_each_missing_component(missing: str) -> None:
    components = tuple(
        item for item in manifest().components if item.component != missing
    )
    incomplete = SystemManifest(components, NOW)
    assert incomplete.complete is False
    assert incomplete.missing_required_components == (missing,)


@pytest.mark.parametrize(
    "attribute",
    [
        "forecast_ready",
        "feedback_ready",
        "memory_ready",
        "digital_twin_ready",
        "calibration_ready",
        "strategy_ready",
        "compiler_ready",
        "safety_ready",
        "executor_ready",
    ],
)
def test_each_readiness_failure_holds_release(attribute: str) -> None:
    readiness = replace(ReadinessEvidence(), **{attribute: False})
    result = OperationalReleaseGate().review(request(readiness=readiness))
    assert result.status is ReleaseStatus.HELD
    assert any(
        not gate.passed and gate.code.value == attribute
        for gate in result.gates
    )


@pytest.mark.parametrize(
    ("maximum", "requested", "expected"),
    [
        (OperationMode.OBSERVE, OperationMode.OBSERVE, ReleaseStatus.RELEASED),
        (OperationMode.OBSERVE, OperationMode.ADVISE, ReleaseStatus.REJECTED),
        (OperationMode.ADVISE, OperationMode.ADVISE, ReleaseStatus.RELEASED),
        (OperationMode.SUPERVISED, OperationMode.SUPERVISED, ReleaseStatus.HELD),
        (OperationMode.AUTONOMOUS, OperationMode.AUTONOMOUS, ReleaseStatus.HELD),
    ],
)
def test_mode_policy(maximum: OperationMode, requested: OperationMode, expected: ReleaseStatus) -> None:
    policy = ReleasePolicy(maximum_mode=maximum)
    result = OperationalReleaseGate(policy).review(request(mode=requested))
    assert result.status is expected


@pytest.mark.parametrize(
    ("mode", "approved", "authorized", "expected"),
    [
        (OperationMode.ADVISE, False, False, ReleaseStatus.RELEASED),
        (OperationMode.SUPERVISED, False, False, ReleaseStatus.HELD),
        (OperationMode.SUPERVISED, True, False, ReleaseStatus.RELEASED),
        (OperationMode.AUTONOMOUS, True, False, ReleaseStatus.HELD),
        (OperationMode.AUTONOMOUS, True, True, ReleaseStatus.RELEASED),
    ],
)
def test_approval_matrix(
    mode: OperationMode,
    approved: bool,
    authorized: bool,
    expected: ReleaseStatus,
) -> None:
    policy = ReleasePolicy(maximum_mode=OperationMode.AUTONOMOUS)
    result = OperationalReleaseGate(policy).review(
        request(
            mode=mode,
            operator_approved=approved,
            autonomy_authorized=authorized,
        )
    )
    assert result.status is expected


@pytest.mark.parametrize(
    ("generated_at", "expected"),
    [
        (NOW - timedelta(minutes=14, seconds=59), ReleaseStatus.RELEASED),
        (NOW - timedelta(minutes=15), ReleaseStatus.RELEASED),
        (NOW - timedelta(minutes=15, seconds=1), ReleaseStatus.HELD),
        (NOW + timedelta(seconds=30), ReleaseStatus.RELEASED),
        (NOW + timedelta(seconds=31), ReleaseStatus.HELD),
    ],
)
def test_freshness_boundaries(generated_at: datetime, expected: ReleaseStatus) -> None:
    decision = replace(FakeDecision(), generated_at=generated_at)
    result = OperationalReleaseGate().review(request(decision=decision))
    assert result.status is expected


@pytest.mark.parametrize(
    ("feasible", "require_feasible", "expected"),
    [
        (True, True, ReleaseStatus.RELEASED),
        (False, True, ReleaseStatus.HELD),
        (False, False, ReleaseStatus.RELEASED),
    ],
)
def test_feasibility_policy(
    feasible: bool,
    require_feasible: bool,
    expected: ReleaseStatus,
) -> None:
    evaluation = replace(FakeEvaluation(), feasible=feasible)
    decision = replace(FakeDecision(), selected=evaluation, alternatives=(evaluation,))
    policy = ReleasePolicy(require_feasible=require_feasible)
    result = OperationalReleaseGate(policy).review(request(decision=decision))
    assert result.status is expected


@pytest.mark.parametrize(
    ("count", "magnitude", "required", "expected"),
    [
        (0, 0.0, True, ReleaseStatus.RELEASED),
        (1, 0.0, True, ReleaseStatus.HELD),
        (0, 0.1, True, ReleaseStatus.HELD),
        (2, 1.5, False, ReleaseStatus.RELEASED),
    ],
)
def test_violation_policy(
    count: int,
    magnitude: float,
    required: bool,
    expected: ReleaseStatus,
) -> None:
    metrics = replace(
        FakeMetrics(),
        violation_count=count,
        violation_magnitude=magnitude,
    )
    evaluation = replace(FakeEvaluation(), metrics=metrics)
    decision = replace(FakeDecision(), selected=evaluation, alternatives=(evaluation,))
    policy = ReleasePolicy(require_zero_violations=required)
    result = OperationalReleaseGate(policy).review(request(decision=decision))
    assert result.status is expected


@pytest.mark.parametrize(
    ("score", "maximum", "expected"),
    [
        (1.0, None, ReleaseStatus.RELEASED),
        (1.0, 1.0, ReleaseStatus.RELEASED),
        (1.0001, 1.0, ReleaseStatus.HELD),
    ],
)
def test_score_policy(score: float, maximum: float | None, expected: ReleaseStatus) -> None:
    metrics = replace(FakeMetrics(), objective_score=score)
    evaluation = replace(FakeEvaluation(), metrics=metrics)
    decision = replace(FakeDecision(), selected=evaluation, alternatives=(evaluation,))
    policy = ReleasePolicy(maximum_objective_score=maximum)
    result = OperationalReleaseGate(policy).review(request(decision=decision))
    assert result.status is expected


@pytest.mark.parametrize(
    ("objective", "allowed", "expected"),
    [
        ("balanced", (), ReleaseStatus.RELEASED),
        ("balanced", ("balanced",), ReleaseStatus.RELEASED),
        ("cost", ("balanced",), ReleaseStatus.HELD),
    ],
)
def test_objective_allowlist(
    objective: str,
    allowed: tuple[str, ...],
    expected: ReleaseStatus,
) -> None:
    candidate = replace(FakeCandidate(), objective=objective)
    evaluation = replace(FakeEvaluation(), candidate=candidate)
    decision = replace(FakeDecision(), selected=evaluation, alternatives=(evaluation,))
    policy = ReleasePolicy(allowed_objectives=allowed)
    result = OperationalReleaseGate(policy).review(request(decision=decision))
    assert result.status is expected


@pytest.mark.parametrize(
    ("field", "allowed", "expected"),
    [
        ("policy_version", ("strategy-policy-1",), ReleaseStatus.RELEASED),
        ("policy_version", ("strategy-policy-2",), ReleaseStatus.HELD),
        ("parameter_version", ("twin-parameters-1",), ReleaseStatus.RELEASED),
        ("parameter_version", ("twin-parameters-2",), ReleaseStatus.HELD),
    ],
)
def test_version_allowlists(
    field: str,
    allowed: tuple[str, ...],
    expected: ReleaseStatus,
) -> None:
    kwargs = {f"allowed_{field}s": allowed}
    policy = ReleasePolicy(**kwargs)
    result = OperationalReleaseGate(policy).review(request())
    assert result.status is expected


@pytest.mark.parametrize(
    "bad_decision",
    [
        SimpleNamespace(),
        SimpleNamespace(decision_id="x"),
        SimpleNamespace(
            decision_id="x",
            generated_at=NOW,
            selected=SimpleNamespace(),
            alternatives=(),
            policy_version="p",
            parameter_version="m",
        ),
    ],
)
def test_invalid_decision_shape_is_rejected(bad_decision: object) -> None:
    result = OperationalReleaseGate().review(request(decision=bad_decision))
    assert result.status is ReleaseStatus.REJECTED
    assert result.intent is None
    assert GateCode.DECISION_SHAPE in {gate.code for gate in result.failed_gates}


def test_released_decision_targets_compiler_not_devices() -> None:
    result = OperationalReleaseGate().review(request())
    assert result.released
    assert result.intent is not None
    assert result.intent.compiler_target == "heos.decision_compiler"
    assert result.intent.control_payload == (
        ("battery_power_kw", 1.0),
        ("ev_charge_kw", 2.0),
        ("hvac_thermal_kw", 3.0),
    )


def test_release_id_is_deterministic() -> None:
    gate = OperationalReleaseGate()
    first = gate.review(request())
    second = gate.review(request())
    assert first == second


def test_release_id_changes_with_mode() -> None:
    policy = ReleasePolicy(maximum_mode=OperationMode.SUPERVISED)
    gate = OperationalReleaseGate(policy)
    advise = gate.review(request(mode=OperationMode.ADVISE))
    supervised = gate.review(
        request(mode=OperationMode.SUPERVISED, operator_approved=True)
    )
    assert advise.release_id != supervised.release_id


def test_serialization_round_trip_for_released_decision() -> None:
    decision = OperationalReleaseGate().review(request())
    assert loads_release_decision(dumps_release_decision(decision)) == decision


def test_serialization_round_trip_for_held_decision() -> None:
    decision = OperationalReleaseGate().review(
        request(readiness=replace(ReadinessEvidence(), safety_ready=False))
    )
    assert loads_release_decision(dumps_release_decision(decision)) == decision


def test_repository_is_append_only_and_idempotent() -> None:
    repository = InMemoryReleaseRepository()
    decision = OperationalReleaseGate().review(request())
    assert repository.append(decision) is decision
    assert repository.append(decision) is decision
    assert len(repository) == 1


def test_repository_rejects_same_id_with_different_content() -> None:
    repository = InMemoryReleaseRepository()
    decision = OperationalReleaseGate().review(request())
    repository.append(decision)
    altered = replace(decision, explanation="different explanation")
    with pytest.raises(ValueError, match="different content"):
        repository.append(altered)


def test_repository_queries() -> None:
    gate = OperationalReleaseGate()
    released = gate.review(request())
    held = gate.review(
        request(
            evaluated_at=NOW + timedelta(seconds=1),
            readiness=replace(ReadinessEvidence(), executor_ready=False),
        )
    )
    repository = InMemoryReleaseRepository((released, held))
    assert repository.by_status(ReleaseStatus.RELEASED) == (released,)
    assert repository.by_status(ReleaseStatus.HELD) == (held,)
    assert repository.by_source_decision("strategy-decision-1") == (released, held)


def test_engine_persists_review() -> None:
    engine = OperationalReleaseEngine()
    decision = engine.evaluate(request())
    assert engine.repository.get(decision.release_id) == decision


def test_control_payload_supports_regular_objects() -> None:
    control = SimpleNamespace(z=3, a=1.5, ignored="x")
    assert control_payload(control) == (("a", 1.5), ("z", 3.0))


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_control_payload_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        control_payload(SimpleNamespace(power=value))


def test_decision_shape_requires_minimum_alternatives() -> None:
    errors = decision_shape_errors(FakeDecision(), minimum_alternatives=2)
    assert "requires at least 2 alternatives; got 1" in errors


@pytest.mark.parametrize(
    "factory",
    [
        lambda: ComponentVersion("", "1"),
        lambda: ComponentVersion("forecast", ""),
        lambda: SystemManifest(
            (
                ComponentVersion("forecast", "1"),
                ComponentVersion("forecast", "2"),
            ),
            NOW,
        ),
        lambda: SystemManifest((), datetime(2026, 1, 1)),  # noqa: DTZ001
        lambda: ReleasePolicy(maximum_decision_age=timedelta()),
        lambda: ReleasePolicy(maximum_future_skew=timedelta(seconds=-1)),
        lambda: ReleasePolicy(minimum_alternatives=0),
        lambda: ReleasePolicy(maximum_objective_score=nan),
        lambda: OperationalRequest(
            FakeDecision(),
            OperationMode.ADVISE,
            datetime(2026, 1, 1),  # noqa: DTZ001
            manifest(),
        ),
    ],
)
def test_model_validation_rejects_invalid_values(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()


def test_execution_intent_requires_future_expiry() -> None:
    with pytest.raises(ValueError, match="not_after"):
        ExecutionIntent(
            intent_id="i",
            source_decision_id="d",
            candidate_id="c",
            requested_mode=OperationMode.ADVISE,
            created_at=NOW,
            not_after=NOW,
            compiler_target="compiler",
            control_payload=(("power", 1.0),),
        )


def test_release_decision_requires_intent_when_released() -> None:
    with pytest.raises(ValueError, match="require an intent"):
        ReleaseDecision(
            release_id="r",
            source_decision_id="d",
            evaluated_at=NOW,
            requested_mode=OperationMode.ADVISE,
            status=ReleaseStatus.RELEASED,
            gates=(GateResult(GateCode.MODE_ALLOWED, True, True, "ok"),),
            policy_version="p",
            manifest_schema_version="m",
            intent=None,
            explanation="x",
        )


def test_standard_manifest_is_complete_and_sorted() -> None:
    system_manifest = manifest()
    assert system_manifest.complete
    assert tuple(name for name, _ in system_manifest.versions) == tuple(
        sorted(name for name, _ in system_manifest.versions)
    )
