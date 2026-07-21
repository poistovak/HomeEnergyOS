from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DecisionMemoryRecord:
    command_id: str
    decision: str
    outcome: str
    expected_value: float
    actual_value: float | None
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

        if not self.outcome.strip():
            raise ValueError(
                "outcome must not be empty"
            )


class DecisionMemory:

    def __init__(self) -> None:
        self._records: list[DecisionMemoryRecord] = []

    def add(
        self,
        record: DecisionMemoryRecord,
    ) -> None:
        self._records.append(record)

    def find(
        self,
        command_id: str,
    ) -> list[DecisionMemoryRecord]:
        return [
            record
            for record in self._records
            if record.command_id == command_id
        ]

    def all(
        self,
    ) -> list[DecisionMemoryRecord]:
        return list(self._records)