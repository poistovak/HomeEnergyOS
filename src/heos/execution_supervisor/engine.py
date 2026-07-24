from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256

from .ledger import ExecutionLedger
from .models import ApprovalToken, ContinuityDirective, ExecutionCertificate
from .policy import ExecutionPolicy


def directive_digest(directive: ContinuityDirective) -> str:
    return sha256(json.dumps(asdict(directive), sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(slots=True)
class ExecutionSupervisor:
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    ledger: ExecutionLedger = field(default_factory=ExecutionLedger)

    def supervise(self, directive: ContinuityDirective, *, now: int, approval: ApprovalToken | None = None) -> ExecutionCertificate:
        command = self.policy.build_command(directive, now=now, approval=approval)
        entries = self.ledger.entries()
        certificate = ExecutionCertificate.issue(
            command=command,
            directive_digest=directive_digest(directive),
            policy_version=self.policy.version,
            previous_digest=entries[-1].digest if entries else None,
        )
        self.ledger.append(certificate)
        return certificate
