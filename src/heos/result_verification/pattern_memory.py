from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PatternMemoryRecord:
    pattern: str
    success_rate: float


class PatternMemory:

    def __init__(self):
        self._records: list[PatternMemoryRecord] = []

    def add(
        self,
        record: PatternMemoryRecord,
    ) -> None:
        self._records.append(record)

    def all(self) -> list[PatternMemoryRecord]:
        return list(self._records)