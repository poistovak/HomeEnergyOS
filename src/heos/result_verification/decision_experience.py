from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DecisionExperience:
    command_id: str
    decision: str
    context: dict[str, object]
    outcome: str
    expected_value: float
    actual_value: float
    success: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.command_id.strip():
            raise ValueError(
                "command_id must not be empty"
            )

        if not self.decision.strip():
            raise ValueError(
                "decision must not be empty"
            )

        if not self.context:
            raise ValueError(
                "context must not be empty"
            )

        if not self.outcome.strip():
            raise ValueError(
                "outcome must not be empty"
            )

        if not math.isfinite(self.expected_value):
            raise ValueError(
                "expected_value must be finite"
            )

        if not math.isfinite(self.actual_value):
            raise ValueError(
                "actual_value must be finite"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )


class DecisionExperienceMemory:

    def __init__(self) -> None:
        self._experiences: list[DecisionExperience] = []

    def add(
        self,
        experience: DecisionExperience,
    ) -> None:
        self._experiences.append(experience)

    def all(
        self,
    ) -> tuple[DecisionExperience, ...]:
        return tuple(self._experiences)

    def count(
        self,
    ) -> int:
        return len(self._experiences)

    def for_decision(
        self,
        decision: str,
    ) -> tuple[DecisionExperience, ...]:
        return tuple(
            experience
            for experience in self._experiences
            if experience.decision == decision
        )