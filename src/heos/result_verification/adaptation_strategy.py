from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdaptationDecision:
    strategy: str
    accepted: bool
    confidence: float


class AdaptationStrategyEngine:

    def evaluate(
        self,
        strategy: str,
        confidence: float,
    ) -> AdaptationDecision:

        if not strategy.strip():
            raise ValueError(
                "strategy must not be empty"
            )

        if not 0 <= confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        return AdaptationDecision(
            strategy=strategy,
            accepted=confidence >= 0.5,
            confidence=confidence,
        )