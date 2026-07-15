from __future__ import annotations

from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from .compare import compare_records
from .models import (
    ComparisonRecord,
    DecisionRecord,
    ExperienceCandidate,
    OutcomeRecord,
)
from .repository import FeedbackRepository
from .scoring import FeedbackScoringPolicy


class FeedbackEngine:
    def __init__(
        self,
        repository: FeedbackRepository,
        *,
        policy: FeedbackScoringPolicy | None = None,
    ) -> None:
        self._repository = repository
        self._policy = policy or FeedbackScoringPolicy()

    def capture_decision(self, record: DecisionRecord) -> DecisionRecord:
        self._repository.append_decision(record)
        return record

    def capture_outcome(self, record: OutcomeRecord) -> OutcomeRecord:
        self._repository.append_outcome(record)
        return record

    def compare(
        self,
        decision_record_id: str,
        outcome_record_id: str,
        *,
        compared_at: datetime,
    ) -> ComparisonRecord:
        decision = self._repository.get_decision(decision_record_id)
        outcome = self._repository.get_outcome(outcome_record_id)
        comparison = compare_records(
            decision,
            outcome,
            compared_at=compared_at,
            policy=self._policy,
        )
        self._repository.append_comparison(comparison)
        return comparison

    def materialize_experience(
        self,
        comparison_record_id: str,
        *,
        created_at: datetime,
    ) -> ExperienceCandidate:
        comparison = self._repository.get_comparison(comparison_record_id)
        decision = self._repository.get_decision(comparison.decision_record_id)
        outcome = self._repository.get_outcome(comparison.outcome_record_id)
        features = {
            f"predicted.{key}": value for key, value in decision.predicted_state.items()
        }
        features.update(
            {
                "metric.prediction_error": comparison.metrics.prediction_error,
                "metric.execution_error": comparison.metrics.execution_error,
                "metric.timing_error": comparison.metrics.timing_error,
                "metric.constraint_error": comparison.metrics.constraint_error,
                "metric.energy_error": comparison.metrics.energy_error,
            }
        )
        targets = {f"actual.{key}": value for key, value in outcome.actual_state.items()}
        identifier = uuid5(
            NAMESPACE_URL,
            f"heos-experience:{comparison.record_id}",
        )
        candidate = ExperienceCandidate(
            record_id=str(identifier),
            decision_record_id=decision.record_id,
            outcome_record_id=outcome.record_id,
            comparison_record_id=comparison.record_id,
            created_at=created_at,
            features=features,
            targets=targets,
            quality_score=comparison.metrics.overall_score * comparison.confidence,
            classification=comparison.classification,
            versions=decision.versions,
            explanation=comparison.explanation,
        )
        self._repository.append_experience(candidate)
        return candidate
