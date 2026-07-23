from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrustDecayResult:
    recommendation: str
    trust: float
    decay_factor: float


class DecisionTrustDecayEngine:

    def apply(
        self,
        recommendation: str,
        trust: float,
        decay_factor: float = 0.95,
    ) -> TrustDecayResult:

        if not recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not 0 <= trust <= 1:
            raise ValueError(
                "trust must be between 0 and 1"
            )

        if not 0 < decay_factor <= 1:
            raise ValueError(
                "decay_factor must be between 0 and 1"
            )

        return TrustDecayResult(
            recommendation=recommendation,
            trust=round(
                trust * decay_factor,
                10,
            ),
            decay_factor=decay_factor,
        )