from __future__ import annotations

from datetime import datetime
from math import isclose
from uuid import NAMESPACE_URL, uuid5

from .models import (
    ActionRecord,
    ComparisonMetrics,
    ComparisonRecord,
    DecisionRecord,
    ExecutionStatus,
    OutcomeClassification,
    OutcomeRecord,
)
from .scoring import FeedbackScoringPolicy


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalized_error(predicted: float, actual: float) -> float:
    denominator = max(abs(predicted), abs(actual), 1.0)
    return _clamp(abs(predicted - actual) / denominator)


def _state_error(
    predicted: dict[str, float] | object,
    actual: dict[str, float] | object,
    *,
    keys: tuple[str, ...] | None = None,
) -> float:
    predicted_map = dict(predicted)  # type: ignore[arg-type]
    actual_map = dict(actual)  # type: ignore[arg-type]
    shared = sorted(set(predicted_map) & set(actual_map))
    if keys is not None:
        shared = [key for key in shared if key in keys]
    if not shared:
        return 0.0
    return round(
        sum(_normalized_error(predicted_map[key], actual_map[key]) for key in shared)
        / len(shared),
        6,
    )


def _energy_keys(*mappings: object) -> tuple[str, ...]:
    keys: set[str] = set()
    for mapping in mappings:
        for key in dict(mapping):  # type: ignore[arg-type]
            normalized = key.lower()
            if "energy" in normalized or normalized.endswith(("_wh", "_kwh")):
                keys.add(key)
    return tuple(sorted(keys))


def _action_map(actions: tuple[ActionRecord, ...]) -> dict[tuple[str, str], ActionRecord]:
    return {action.identity: action for action in actions}


def _execution_error(
    planned: tuple[ActionRecord, ...],
    executed: tuple[ActionRecord, ...],
) -> float:
    if not planned and not executed:
        return 0.0
    planned_map = _action_map(planned)
    executed_map = _action_map(executed)
    identities = set(planned_map) | set(executed_map)
    if not identities:
        return 0.0
    penalties: list[float] = []
    for identity in sorted(identities):
        expected = planned_map.get(identity)
        actual = executed_map.get(identity)
        if expected is None or actual is None:
            penalties.append(1.0)
            continue
        if expected.target is None and actual.target is None:
            penalties.append(0.0)
            continue
        if expected.target is None or actual.target is None:
            penalties.append(1.0)
            continue
        penalties.append(_normalized_error(expected.target, actual.target))
    return round(sum(penalties) / len(penalties), 6)


def _timing_error(decision: DecisionRecord, outcome: OutcomeRecord) -> float:
    expected_duration = (decision.effective_until - decision.effective_from).total_seconds()
    start_delta = abs((outcome.window_start - decision.effective_from).total_seconds())
    end_delta = abs((outcome.window_end - decision.effective_until).total_seconds())
    return round(_clamp((start_delta + end_delta) / (2 * expected_duration)), 6)


def _constraint_error(outcome: OutcomeRecord) -> float:
    if outcome.constraints_satisfied and not outcome.violations:
        return 0.0
    if outcome.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
        return 1.0
    return _clamp(0.5 + 0.1 * len(outcome.violations))


def _confidence(decision: DecisionRecord, outcome: OutcomeRecord) -> float:
    predicted_keys = set(decision.predicted_state)
    actual_keys = set(outcome.actual_state)
    union = predicted_keys | actual_keys
    state_coverage = len(predicted_keys & actual_keys) / len(union) if union else 1.0
    action_union = set(_action_map(decision.planned_actions)) | set(
        _action_map(outcome.executed_actions)
    )
    action_coverage = (
        len(
            set(_action_map(decision.planned_actions))
            & set(_action_map(outcome.executed_actions))
        )
        / len(action_union)
        if action_union
        else 1.0
    )
    return round(0.7 * state_coverage + 0.3 * action_coverage, 6)


def _root_causes(metrics: ComparisonMetrics) -> tuple[str, ...]:
    candidates = {
        "forecast_miss": metrics.prediction_error,
        "execution_mismatch": metrics.execution_error,
        "timing_drift": metrics.timing_error,
        "constraint_violation": metrics.constraint_error,
        "energy_miss": metrics.energy_error,
    }
    causes = [name for name, value in candidates.items() if value >= 0.25]
    if not causes and not isclose(metrics.overall_score, 1.0):
        causes = [max(candidates, key=candidates.get)]
    return tuple(sorted(causes))


def compare_records(
    decision: DecisionRecord,
    outcome: OutcomeRecord,
    *,
    compared_at: datetime,
    policy: FeedbackScoringPolicy | None = None,
) -> ComparisonRecord:
    if outcome.decision_record_id != decision.record_id:
        raise ValueError("outcome does not belong to decision")
    if compared_at.tzinfo is None or compared_at.utcoffset() is None:
        raise ValueError("compared_at must be timezone-aware")
    active_policy = policy or FeedbackScoringPolicy()
    prediction_error = _state_error(decision.predicted_state, outcome.actual_state)
    energy_keys = _energy_keys(decision.predicted_state, outcome.actual_state)
    energy_error = _state_error(
        decision.predicted_state,
        outcome.actual_state,
        keys=energy_keys,
    )
    execution_error = _execution_error(decision.planned_actions, outcome.executed_actions)
    timing_error = _timing_error(decision, outcome)
    constraint_error = _constraint_error(outcome)
    overall_score = active_policy.overall_score(
        prediction_error=prediction_error,
        execution_error=execution_error,
        timing_error=timing_error,
        constraint_error=constraint_error,
        energy_error=energy_error,
    )
    metrics = ComparisonMetrics(
        prediction_error=prediction_error,
        execution_error=execution_error,
        timing_error=timing_error,
        constraint_error=constraint_error,
        energy_error=energy_error,
        overall_score=overall_score,
    )
    classification = active_policy.classify(metrics)
    if outcome.status in (ExecutionStatus.FAILED, ExecutionStatus.BLOCKED):
        classification = OutcomeClassification.FAILED
    causes = _root_causes(metrics)
    explanation = (
        f"Decision {decision.decision_id} scored {overall_score:.3f}; "
        f"classification={classification.value}; "
        f"root_causes={','.join(causes) if causes else 'none'}."
    )
    identifier = uuid5(
        NAMESPACE_URL,
        f"heos-feedback:{decision.record_id}:{outcome.record_id}",
    )
    return ComparisonRecord(
        record_id=str(identifier),
        decision_record_id=decision.record_id,
        outcome_record_id=outcome.record_id,
        compared_at=compared_at,
        metrics=metrics,
        classification=classification,
        root_causes=causes,
        confidence=_confidence(decision, outcome),
        explanation=explanation,
    )
