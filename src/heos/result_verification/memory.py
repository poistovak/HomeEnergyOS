from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(slots=True)
class LearningMemory:
    _records: list[LearningRecord]

    def __init__(self) -> None:
        self._records = []

    def add(
        self,
        record: LearningRecord,
    ) -> None:
        self._records.append(record)

    def all(
        self,
    ) -> tuple[LearningRecord, ...]:
        return tuple(self._records)

    def count(self) -> int:
        return len(self._records)

    def latest(
        self,
    ) -> LearningRecord | None:
        if not self._records:
            return None

        return self._records[-1]