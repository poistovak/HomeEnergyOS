from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import CertifiedDecision


class ProofRepository(Protocol):
    def append(self, decision: CertifiedDecision) -> CertifiedDecision: ...

    def get(self, certificate_id: str) -> CertifiedDecision | None: ...

    def all(self) -> tuple[CertifiedDecision, ...]: ...


class InMemoryProofRepository:
    def __init__(self, initial: Iterable[CertifiedDecision] = ()) -> None:
        self._records: dict[str, CertifiedDecision] = {}
        self._order: list[str] = []
        for decision in initial:
            self.append(decision)

    def append(self, decision: CertifiedDecision) -> CertifiedDecision:
        key = decision.certificate.certificate_id
        existing = self._records.get(key)
        if existing is not None:
            if existing != decision:
                raise ValueError("certificate_id already exists with different content")
            return existing
        self._records[key] = decision
        self._order.append(key)
        return decision

    def get(self, certificate_id: str) -> CertifiedDecision | None:
        return self._records.get(str(certificate_id))

    def all(self) -> tuple[CertifiedDecision, ...]:
        return tuple(self._records[item] for item in self._order)

    def by_release(self, release_id: str) -> tuple[CertifiedDecision, ...]:
        normalized = str(release_id)
        return tuple(item for item in self.all() if item.certificate.release_id == normalized)

    def last(self) -> CertifiedDecision | None:
        return self._records[self._order[-1]] if self._order else None

    def __len__(self) -> int:
        return len(self._order)
