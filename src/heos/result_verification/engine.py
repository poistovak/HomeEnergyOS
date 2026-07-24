from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .ledger import VerificationLedger
from .models import Observation, ResultExpectation, VerificationDecision
from .policy import ResultVerificationPolicy
from .verifier import ResultVerifier


@dataclass(slots=True)
class ResultVerificationEngine:
    policy: ResultVerificationPolicy = field(default_factory=ResultVerificationPolicy)
    ledger: VerificationLedger = field(default_factory=VerificationLedger)

    def verify(
        self,
        expectation: ResultExpectation,
        observations: Iterable[Observation],
        *,
        attempts_used: int = 0,
        now: int | None = None,
    ) -> VerificationDecision:
        decision = ResultVerifier(self.policy).verify(
            expectation,
            observations,
            attempts_used=attempts_used,
            now=now,
        )
        self.ledger.append(decision)
        return decision
