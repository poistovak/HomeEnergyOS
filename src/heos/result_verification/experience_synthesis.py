from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExperienceSynthesis:
    recommendation: str
    confidence: float


class ExperienceSynthesisEngine:

    def synthesize(
        self,
        recommendation: str,
        scores: list[float],
    ) -> ExperienceSynthesis:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not scores:
            raise ValueError(
                "scores must not be empty"
            )

        confidence = round(
            sum(scores) / len(scores),
            10,
        )

        return ExperienceSynthesis(
            recommendation=recommendation,
            confidence=confidence,
        )