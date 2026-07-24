from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256

from .ledger import OutcomeLedger
from .models import ExecutionEvidence, ExpectedOutcome, OutcomeCertificate
from .policy import VerificationPolicy


def object_digest(value: object) -> str:
    return sha256(json.dumps(asdict(value), sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(slots=True)
class OutcomeVerifier:
    policy: VerificationPolicy = field(default_factory=VerificationPolicy)
    ledger: OutcomeLedger = field(default_factory=OutcomeLedger)

    def verify_outcome(self, expected: ExpectedOutcome, evidence: ExecutionEvidence) -> OutcomeCertificate:
        result = self.policy.evaluate(expected, evidence)
        entries = self.ledger.entries()
        certificate = OutcomeCertificate.issue(
            result=result,
            expectation_digest=object_digest(expected),
            evidence_digest=object_digest(evidence),
            policy_version=self.policy.version,
            previous_digest=entries[-1].digest if entries else None,
        )
        self.ledger.append(certificate)
        return certificate
