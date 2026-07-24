from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from .classifier import build_incident, incident_digest
from .ledger import IncidentLedger
from .models import FaultSignal, RecoveryCertificate
from .policy import RecoveryPolicy


@dataclass(slots=True)
class ResilienceEngine:
    policy: RecoveryPolicy = field(default_factory=RecoveryPolicy)
    ledger: IncidentLedger = field(default_factory=IncidentLedger)

    def assess(
        self,
        signals: Iterable[FaultSignal],
        *,
        now: int,
    ) -> RecoveryCertificate:
        incident = build_incident(signals)
        decision = self.policy.evaluate(incident, now=now)
        previous_digest = (
            self.ledger.entries()[-1].digest if self.ledger.entries() else None
        )
        certificate = RecoveryCertificate.issue(
            decision=decision,
            incident_digest=incident_digest(incident),
            policy_version=self.policy.version,
            previous_digest=previous_digest,
        )
        self.ledger.append(certificate)
        return certificate
