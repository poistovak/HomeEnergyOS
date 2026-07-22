from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DecisionFeedback:
    command_id: str
    recommendation: str
    outcome: str
    success: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.command_id.strip():
            raise ValueError(
                "command_id must not be empty"
            )

        if not self.recommendation.strip():
            raise ValueError(
                "recommendation must not be empty"
            )

        if not self.outcome.strip():
            raise ValueError(
                "outcome must not be empty"
            )


class DecisionFeedbackMemory:

    def __init__(self) -> None:
        self._feedback: list[DecisionFeedback] = []

    def add(
        self,
        feedback: DecisionFeedback,
    ) -> None:
        self._feedback.append(feedback)

    def all(
        self,
    ) -> list[DecisionFeedback]:
        return list(self._feedback)

    def successful(
        self,
    ) -> list[DecisionFeedback]:
        return [
            item
            for item in self._feedback
            if item.success
        ]