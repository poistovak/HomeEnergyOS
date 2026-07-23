from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoalStrategy:
    goal: str
    priority: float


class GoalStrategyEngine:

    def evaluate(
        self,
        goal: str,
        priority: float,
    ) -> GoalStrategy:

        if not goal.strip():
            raise ValueError(
                "goal must not be empty"
            )

        if not 0 <= priority <= 1:
            raise ValueError(
                "priority must be between 0 and 1"
            )

        return GoalStrategy(
            goal=goal,
            priority=priority,
        )