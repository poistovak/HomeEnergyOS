from __future__ import annotations

from dataclasses import dataclass

from .decision_memory import (
    DecisionMemory,
    DecisionMemoryRecord,
)


@dataclass(frozen=True, slots=True)
class DecisionQuery:
    decision: str | None = None
    outcome: str | None = None
    success_only: bool = False


class DecisionMemoryQuery:

    def __init__(
        self,
        memory: DecisionMemory,
    ) -> None:
        self.memory = memory

    def search(
        self,
        query: DecisionQuery,
    ) -> list[DecisionMemoryRecord]:

        records = self.memory.all()

        result = []

        for record in records:

            if query.decision and record.decision != query.decision:
                continue

            if query.outcome and record.outcome != query.outcome:
                continue

            if query.success_only and not record.success:
                continue

            result.append(record)

        return result