from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionEvolution:
    recommendation: str
    trend: str
    score: float


class DecisionEvolutionEngine:

    def evaluate(
        self,
        recommendation: str,
        history: list[float],
    ) -> DecisionEvolution:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if len(history) < 2:
            raise ValueError(
                "history requires at least two values"
            )

        first = history[0]
        last = history[-1]

        score = round(
            last - first,
            10,
        )

        if score > 0:
            trend = "improving"
        elif score < 0:
            trend = "declining"
        else:
            trend = "stable"

        return DecisionEvolution(
            recommendation=recommendation,
            trend=trend,
            score=score,
        )