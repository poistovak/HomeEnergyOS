from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningConfidence:
    confidence: float


class ReasoningConfidenceEngine:

    def evaluate(
        self,
        confidence: float,
    ) -> ReasoningConfidence:

        if not 0 <= confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        return ReasoningConfidence(
            confidence=confidence,
        )