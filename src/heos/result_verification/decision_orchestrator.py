from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    recommendation: str
    confidence: float


class DecisionIntelligenceOrchestrator:

    def decide(
        self,
        recommendation: str,
        confidence: float,
    ) -> DecisionOutcome:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not 0 <= confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        return DecisionOutcome(
            recommendation=recommendation,
            confidence=confidence,
        )