from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionPattern:
    recommendation: str
    occurrences: int
    score: float


class DecisionPatternEngine:

    def analyze(
        self,
        recommendation: str,
        history: list[bool],
    ) -> DecisionPattern:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not history:
            raise ValueError(
                "history must not be empty"
            )

        occurrences = len(history)

        score = round(
            sum(history) / occurrences,
            10,
        )

        return DecisionPattern(
            recommendation=recommendation,
            occurrences=occurrences,
            score=score,
        )