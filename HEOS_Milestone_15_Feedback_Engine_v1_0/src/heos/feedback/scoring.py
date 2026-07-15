from __future__ import annotations

from dataclasses import dataclass

from .models import ComparisonMetrics, OutcomeClassification


@dataclass(frozen=True, slots=True)
class FeedbackScoringPolicy:
    prediction_weight: float = 0.30
    execution_weight: float = 0.25
    timing_weight: float = 0.10
    constraint_weight: float = 0.20
    energy_weight: float = 0.15
    excellent_threshold: float = 0.90
    acceptable_threshold: float = 0.75
    degraded_threshold: float = 0.50

    def __post_init__(self) -> None:
        weights = (
            self.prediction_weight,
            self.execution_weight,
            self.timing_weight,
            self.constraint_weight,
            self.energy_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("weights must not be negative")
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("weights must sum to 1.0")
        if not (
            0.0
            <= self.degraded_threshold
            <= self.acceptable_threshold
            <= self.excellent_threshold
            <= 1.0
        ):
            raise ValueError("classification thresholds must be ordered within 0..1")

    def overall_score(
        self,
        *,
        prediction_error: float,
        execution_error: float,
        timing_error: float,
        constraint_error: float,
        energy_error: float,
    ) -> float:
        weighted_error = (
            prediction_error * self.prediction_weight
            + execution_error * self.execution_weight
            + timing_error * self.timing_weight
            + constraint_error * self.constraint_weight
            + energy_error * self.energy_weight
        )
        return round(max(0.0, min(1.0, 1.0 - weighted_error)), 6)

    def classify(self, metrics: ComparisonMetrics) -> OutcomeClassification:
        score = metrics.overall_score
        if score >= self.excellent_threshold:
            return OutcomeClassification.EXCELLENT
        if score >= self.acceptable_threshold:
            return OutcomeClassification.ACCEPTABLE
        if score >= self.degraded_threshold:
            return OutcomeClassification.DEGRADED
        return OutcomeClassification.FAILED
