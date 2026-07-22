from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionTrust:
    recommendation: str
    trust: float
    samples: int


class DecisionTrustEngine:

    def evaluate(
        self,
        recommendation: str,
        confidence_values: list[float],
    ) -> DecisionTrust:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not confidence_values:
            raise ValueError(
                "confidence_values must not be empty"
            )

        trust = round(
            sum(confidence_values)
            / len(confidence_values),
            10,
        )

        return DecisionTrust(
            recommendation=recommendation,
            trust=trust,
            samples=len(confidence_values),
        )