from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from heos.feedback import (
    ActionRecord,
    ComparisonMetrics,
    DecisionRecord,
    ExecutionStatus,
    FeedbackEngine,
    FeedbackQuery,
    FeedbackScoringPolicy,
    InMemoryFeedbackRepository,
    OutcomeClassification,
    OutcomeRecord,
    VersionStamp,
    compare_records,
    outcome_from_runtime_report,
)

START = datetime(2026, 7, 15, 8, 0, tzinfo=UTC)
END = START + timedelta(hours=1)
VERSIONS = VersionStamp(
    schema_version="1.0",
    forecast_version="m14-1.0",
    model_version="physics-0.1",
    policy_version="policy-1",
    compiler_version="m10-1.0",
)


def action(target: float = 3000) -> ActionRecord:
    return ActionRecord("ev.charger", "set_power", target, "W")


def decision(**overrides) -> DecisionRecord:
    values = {
        "record_id": "decision-record-1",
        "decision_id": "decision-1",
        "scenario_id": "charge_ev_now",
        "committed_at": START - timedelta(minutes=1),
        "effective_from": START,
        "effective_until": END,
        "predicted_state": {"grid_energy_kwh": 1.0, "battery_soc": 60.0},
        "planned_actions": (action(),),
        "versions": VERSIONS,
        "context": {"mode": "automatic"},
    }
    values.update(overrides)
    return DecisionRecord(**values)


def outcome(**overrides) -> OutcomeRecord:
    values = {
        "record_id": "outcome-record-1",
        "decision_record_id": "decision-record-1",
        "observed_at": END,
        "window_start": START,
        "window_end": END,
        "actual_state": {"grid_energy_kwh": 1.0, "battery_soc": 60.0},
        "executed_actions": (action(),),
        "status": ExecutionStatus.COMPLETED,
    }
    values.update(overrides)
    return OutcomeRecord(**values)


def test_version_stamp_rejects_empty_version() -> None:
    with pytest.raises(ValueError, match="model_version"):
        VersionStamp("1", "1", "", "1", "1")


def test_action_is_immutable() -> None:
    item = action()
    with pytest.raises(FrozenInstanceError):
        item.action = "stop"  # type: ignore[misc]


def test_action_metadata_is_read_only() -> None:
    item = ActionRecord("ev", "charge", metadata={"source": "compiler"})
    with pytest.raises(TypeError):
        item.metadata["source"] = "manual"  # type: ignore[index]


def test_decision_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="committed_at"):
        decision(committed_at=datetime(2026, 7, 15, 7, 59))


def test_decision_rejects_invalid_window() -> None:
    with pytest.raises(ValueError, match="effective_until"):
        decision(effective_until=START)


def test_decision_state_is_sorted_and_read_only() -> None:
    item = decision(predicted_state={"z": 1, "a": 2})
    assert tuple(item.predicted_state) == ("a", "z")
    with pytest.raises(TypeError):
        item.predicted_state["a"] = 5  # type: ignore[index]


def test_outcome_rejects_invalid_window() -> None:
    with pytest.raises(ValueError, match="window_end"):
        outcome(window_end=START)


def test_metrics_reject_out_of_range_value() -> None:
    with pytest.raises(ValueError, match="prediction_error"):
        ComparisonMetrics(1.1, 0, 0, 0, 0, 0)


def test_policy_rejects_weights_not_summing_to_one() -> None:
    with pytest.raises(ValueError, match="sum"):
        FeedbackScoringPolicy(prediction_weight=0.5)


def test_policy_rejects_unordered_thresholds() -> None:
    with pytest.raises(ValueError, match="ordered"):
        FeedbackScoringPolicy(excellent_threshold=0.6, acceptable_threshold=0.8)


def test_perfect_comparison_scores_one() -> None:
    result = compare_records(decision(), outcome(), compared_at=END)
    assert result.metrics.overall_score == 1.0
    assert result.classification is OutcomeClassification.EXCELLENT
    assert result.root_causes == ()


def test_comparison_is_deterministic() -> None:
    first = compare_records(decision(), outcome(), compared_at=END)
    second = compare_records(decision(), outcome(), compared_at=END + timedelta(minutes=1))
    assert first.record_id == second.record_id
    assert first.metrics == second.metrics


def test_comparison_rejects_wrong_decision_reference() -> None:
    with pytest.raises(ValueError, match="does not belong"):
        compare_records(
            decision(),
            outcome(decision_record_id="other"),
            compared_at=END,
        )


def test_comparison_rejects_naive_compared_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        compare_records(decision(), outcome(), compared_at=datetime(2026, 7, 15, 9))


def test_prediction_error_detects_state_difference() -> None:
    result = compare_records(
        decision(),
        outcome(actual_state={"grid_energy_kwh": 2.0, "battery_soc": 30.0}),
        compared_at=END,
    )
    assert result.metrics.prediction_error == 0.5


def test_energy_error_uses_energy_keys_only() -> None:
    result = compare_records(
        decision(),
        outcome(actual_state={"grid_energy_kwh": 2.0, "battery_soc": 60.0}),
        compared_at=END,
    )
    assert result.metrics.energy_error == 0.5
    assert result.metrics.prediction_error == 0.25


def test_missing_energy_keys_produce_zero_energy_error() -> None:
    result = compare_records(
        decision(predicted_state={"battery_soc": 60}),
        outcome(actual_state={"battery_soc": 50}),
        compared_at=END,
    )
    assert result.metrics.energy_error == 0.0


def test_execution_error_detects_missing_action() -> None:
    result = compare_records(
        decision(),
        outcome(executed_actions=()),
        compared_at=END,
    )
    assert result.metrics.execution_error == 1.0
    assert "execution_mismatch" in result.root_causes


def test_execution_error_detects_target_difference() -> None:
    result = compare_records(
        decision(),
        outcome(executed_actions=(action(1500),)),
        compared_at=END,
    )
    assert result.metrics.execution_error == 0.5


def test_timing_error_detects_shifted_window() -> None:
    result = compare_records(
        decision(),
        outcome(
            window_start=START + timedelta(minutes=30),
            window_end=END + timedelta(minutes=30),
        ),
        compared_at=END + timedelta(minutes=30),
    )
    assert result.metrics.timing_error == 0.5


def test_constraint_error_is_zero_when_satisfied() -> None:
    result = compare_records(decision(), outcome(), compared_at=END)
    assert result.metrics.constraint_error == 0.0


def test_constraint_violation_is_root_cause() -> None:
    result = compare_records(
        decision(),
        outcome(constraints_satisfied=False, violations=("grid_limit",)),
        compared_at=END,
    )
    assert result.metrics.constraint_error == 0.6
    assert "constraint_violation" in result.root_causes


def test_failed_runtime_forces_failed_classification() -> None:
    result = compare_records(
        decision(),
        outcome(
            status=ExecutionStatus.FAILED,
            constraints_satisfied=False,
            violations=("driver_error",),
        ),
        compared_at=END,
    )
    assert result.classification is OutcomeClassification.FAILED


def test_confidence_reflects_partial_state_coverage() -> None:
    result = compare_records(
        decision(),
        outcome(actual_state={"battery_soc": 60}),
        compared_at=END,
    )
    assert result.confidence == 0.65


def test_repository_is_append_only() -> None:
    repository = InMemoryFeedbackRepository()
    repository.append_decision(decision())
    with pytest.raises(ValueError, match="already exists"):
        repository.append_decision(decision())


def test_repository_rejects_orphan_outcome() -> None:
    repository = InMemoryFeedbackRepository()
    with pytest.raises(KeyError):
        repository.append_outcome(outcome())


def test_engine_runs_complete_feedback_cycle() -> None:
    repository = InMemoryFeedbackRepository()
    engine = FeedbackEngine(repository)
    engine.capture_decision(decision())
    engine.capture_outcome(outcome())
    comparison = engine.compare("decision-record-1", "outcome-record-1", compared_at=END)
    experience = engine.materialize_experience(comparison.record_id, created_at=END)
    assert experience.quality_score == 1.0
    assert experience.versions == VERSIONS
    assert experience.features["predicted.battery_soc"] == 60
    assert experience.targets["actual.battery_soc"] == 60


def test_experience_id_is_deterministic() -> None:
    first_repository = InMemoryFeedbackRepository()
    first_engine = FeedbackEngine(first_repository)
    first_engine.capture_decision(decision())
    first_engine.capture_outcome(outcome())
    first_comparison = first_engine.compare(
        "decision-record-1",
        "outcome-record-1",
        compared_at=END,
    )
    first = first_engine.materialize_experience(first_comparison.record_id, created_at=END)

    second_repository = InMemoryFeedbackRepository()
    second_engine = FeedbackEngine(second_repository)
    second_engine.capture_decision(decision())
    second_engine.capture_outcome(outcome())
    second_comparison = second_engine.compare(
        "decision-record-1",
        "outcome-record-1",
        compared_at=END,
    )
    second = second_engine.materialize_experience(second_comparison.record_id, created_at=END)
    assert first.record_id == second.record_id


def test_query_filters_by_scenario() -> None:
    repository = InMemoryFeedbackRepository()
    engine = FeedbackEngine(repository)
    engine.capture_decision(decision())
    engine.capture_outcome(outcome())
    engine.compare("decision-record-1", "outcome-record-1", compared_at=END)
    assert len(repository.comparisons(FeedbackQuery(scenario_id="charge_ev_now"))) == 1
    assert repository.comparisons(FeedbackQuery(scenario_id="other")) == ()


def test_query_filters_by_classification() -> None:
    repository = InMemoryFeedbackRepository()
    engine = FeedbackEngine(repository)
    engine.capture_decision(decision())
    engine.capture_outcome(outcome())
    engine.compare("decision-record-1", "outcome-record-1", compared_at=END)
    assert len(
        repository.comparisons(
            FeedbackQuery(classification=OutcomeClassification.EXCELLENT)
        )
    ) == 1


def test_query_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="since"):
        FeedbackQuery(since=datetime(2026, 7, 15, 8))


def test_query_rejects_reverse_range() -> None:
    with pytest.raises(ValueError, match="until"):
        FeedbackQuery(since=END, until=START)


def test_runtime_bridge_maps_completed_report() -> None:
    class Status:
        value = "completed"

    class Entry:
        step_type = "set_power"
        description = "Set EV power"
        success = True
        message = "DRY-RUN"

    class Report:
        status = Status()
        journal = (Entry(),)
        failure_reason = None

    record = outcome_from_runtime_report(
        decision(),
        Report(),
        record_id="runtime-outcome",
        observed_at=END,
        actual_state={"battery_soc": 61},
    )
    assert record.status is ExecutionStatus.COMPLETED
    assert len(record.executed_actions) == 1
    assert record.constraints_satisfied is True


def test_runtime_bridge_maps_failed_report() -> None:
    class Status:
        value = "failed"

    class Report:
        status = Status()
        journal = ()
        failure_reason = "driver rejected command"

    record = outcome_from_runtime_report(
        decision(),
        Report(),
        record_id="runtime-outcome",
        observed_at=END,
        actual_state={},
    )
    assert record.status is ExecutionStatus.FAILED
    assert record.constraints_satisfied is False
    assert record.violations == ("driver rejected command",)


def test_runtime_bridge_unknown_status_is_safe() -> None:
    class Report:
        status = "something-new"
        journal = ()
        failure_reason = None

    record = outcome_from_runtime_report(
        decision(),
        Report(),
        record_id="runtime-outcome",
        observed_at=END,
        actual_state={},
    )
    assert record.status is ExecutionStatus.UNKNOWN


def test_custom_policy_changes_score() -> None:
    policy = FeedbackScoringPolicy(
        prediction_weight=1.0,
        execution_weight=0.0,
        timing_weight=0.0,
        constraint_weight=0.0,
        energy_weight=0.0,
    )
    result = compare_records(
        decision(),
        outcome(actual_state={"grid_energy_kwh": 2.0, "battery_soc": 30.0}),
        compared_at=END,
        policy=policy,
    )
    assert result.metrics.overall_score == 0.5


def test_explanation_is_machine_traceable() -> None:
    result = compare_records(decision(), outcome(), compared_at=END)
    assert "decision-1" in result.explanation
    assert "classification=excellent" in result.explanation
