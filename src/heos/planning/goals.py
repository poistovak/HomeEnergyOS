"""Goal model used to score future scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GoalKind(StrEnum):
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_SELF_CONSUMPTION = "maximize_self_consumption"
    PREPARE_EV = "prepare_ev"
    PROTECT_GRID = "protect_grid"
    PRESERVE_STORAGE = "preserve_storage"


@dataclass(frozen=True, slots=True)
class Goal:
    kind: GoalKind
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("goal weight cannot be negative")


@dataclass(frozen=True, slots=True)
class GoalSet:
    goals: tuple[Goal, ...]

    def __post_init__(self) -> None:
        if not self.goals:
            raise ValueError("GoalSet must contain at least one goal")

    def weight_for(self, kind: GoalKind) -> float:
        return sum(
            goal.weight
            for goal in self.goals
            if goal.kind is kind
        )
