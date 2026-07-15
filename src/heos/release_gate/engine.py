from __future__ import annotations

from .models import OperationalRequest, ReleaseDecision, ReleasePolicy
from .repository import InMemoryReleaseRepository, ReleaseRepository
from .supervisor import OperationalReleaseGate


class OperationalReleaseEngine:
    def __init__(
        self,
        *,
        policy: ReleasePolicy | None = None,
        repository: ReleaseRepository | None = None,
    ) -> None:
        self._gate = OperationalReleaseGate(policy)
        self._repository = repository or InMemoryReleaseRepository()

    @property
    def gate(self) -> OperationalReleaseGate:
        return self._gate

    @property
    def repository(self) -> ReleaseRepository:
        return self._repository

    def evaluate(self, request: OperationalRequest) -> ReleaseDecision:
        decision = self._gate.review(request)
        return self._repository.append(decision)
