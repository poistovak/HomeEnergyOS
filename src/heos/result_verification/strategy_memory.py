from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyMemory:
    strategy: str
    success_rate: float


class StrategyMemoryEngine:

    def remember(
        self,
        strategy: str,
        success_rate: float,
    ) -> StrategyMemory:

        if not strategy.strip():
            raise ValueError(
                "strategy must not be empty"
            )

        if not 0 <= success_rate <= 1:
            raise ValueError(
                "success_rate must be between 0 and 1"
            )

        return StrategyMemory(
            strategy=strategy,
            success_rate=success_rate,
        )