from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from hashlib import sha256

from .ledger import ContinuityLedger
from .models import ContinuityCertificate, RecoverySnapshot
from .policy import ContinuityPolicy


def recovery_digest(recovery: RecoverySnapshot) -> str:
    payload = asdict(recovery)
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(slots=True)
class ContinuityGovernor:
    policy: ContinuityPolicy = field(default_factory=ContinuityPolicy)
    ledger: ContinuityLedger = field(default_factory=ContinuityLedger)

    def govern(
        self,
        recovery: RecoverySnapshot,
        *,
        now: int,
    ) -> ContinuityCertificate:
        plan = self.policy.build_plan(recovery, now=now)
        entries = self.ledger.entries()
        previous_digest = entries[-1].digest if entries else None
        certificate = ContinuityCertificate.issue(
            plan=plan,
            recovery_digest=recovery_digest(recovery),
            policy_version=self.policy.version,
            previous_digest=previous_digest,
        )
        self.ledger.append(certificate)
        return certificate
