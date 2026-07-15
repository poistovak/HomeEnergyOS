from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import ReleaseDecision, ReleaseStatus


class ReleaseRepository(Protocol):
    def append(self, decision: ReleaseDecision) -> ReleaseDecision: ...

    def get(self, release_id: str) -> ReleaseDecision | None: ...

    def all(self) -> tuple[ReleaseDecision, ...]: ...


class InMemoryReleaseRepository:
    def __init__(self, initial: Iterable[ReleaseDecision] = ()) -> None:
        self._records: dict[str, ReleaseDecision] = {}
        self._order: list[str] = []
        for decision in initial:
            self.append(decision)

    def append(self, decision: ReleaseDecision) -> ReleaseDecision:
        existing = self._records.get(decision.release_id)
        if existing is not None:
            if existing != decision:
                raise ValueError("release_id already exists with different content")
            return existing
        self._records[decision.release_id] = decision
        self._order.append(decision.release_id)
        return decision

    def get(self, release_id: str) -> ReleaseDecision | None:
        return self._records.get(str(release_id))

    def all(self) -> tuple[ReleaseDecision, ...]:
        return tuple(self._records[item] for item in self._order)

    def by_status(self, status: ReleaseStatus) -> tuple[ReleaseDecision, ...]:
        normalized = ReleaseStatus(status)
        return tuple(item for item in self.all() if item.status is normalized)

    def by_source_decision(self, decision_id: str) -> tuple[ReleaseDecision, ...]:
        normalized = str(decision_id)
        return tuple(
            item for item in self.all() if item.source_decision_id == normalized
        )

    def __len__(self) -> int:
        return len(self._order)
