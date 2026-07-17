from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Tuple


class RecoveryMode(str, Enum):
    CONTINUE = "continue"
    DEGRADE = "degrade"
    HOLD = "hold"
    FALLBACK = "fallback"
    SAFE_STOP = "safe_stop"


class ContinuityStatus(str, Enum):
    AUTOMATIC = "automatic"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    incident_id: str
    mode: RecoveryMode
    severity: int
    fallback_strategy: str | None
    valid_until: int
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.incident_id.strip():
            raise ValueError("incident_id must not be empty")
        if not 0 <= self.severity <= 100:
            raise ValueError("severity must be between 0 and 100")
        if self.valid_until < 0:
            raise ValueError("valid_until must be non-negative")
        if self.mode is RecoveryMode.FALLBACK and not self.fallback_strategy:
            raise ValueError("fallback mode requires fallback_strategy")


@dataclass(frozen=True, slots=True)
class ContinuityPlan:
    plan_id: str
    incident_id: str
    status: ContinuityStatus
    action: str
    max_attempts: int
    cooldown_seconds: int
    deadline: int
    approval_token_required: bool
    reasons: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise ValueError("plan_id must not be empty")
        if not self.action.strip():
            raise ValueError("action must not be empty")
        if self.max_attempts < 0:
            raise ValueError("max_attempts must be non-negative")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        if self.deadline < 0:
            raise ValueError("deadline must be non-negative")
        if not self.reasons:
            raise ValueError("reasons must not be empty")
        if self.status is ContinuityStatus.BLOCKED and self.max_attempts != 0:
            raise ValueError("blocked plan must have zero attempts")
        if (
            self.status is ContinuityStatus.APPROVAL_REQUIRED
            and not self.approval_token_required
        ):
            raise ValueError("approval-required plan must require an approval token")


@dataclass(frozen=True, slots=True)
class ContinuityCertificate:
    plan: ContinuityPlan
    recovery_digest: str
    policy_version: str
    previous_digest: str | None
    digest: str

    @staticmethod
    def canonical_payload(
        plan: ContinuityPlan,
        recovery_digest: str,
        policy_version: str,
        previous_digest: str | None,
    ) -> str:
        payload = {
            "plan": asdict(plan),
            "recovery_digest": recovery_digest,
            "policy_version": policy_version,
            "previous_digest": previous_digest,
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def issue(
        cls,
        *,
        plan: ContinuityPlan,
        recovery_digest: str,
        policy_version: str,
        previous_digest: str | None = None,
    ) -> "ContinuityCertificate":
        payload = cls.canonical_payload(
            plan,
            recovery_digest,
            policy_version,
            previous_digest,
        )
        digest = sha256(payload.encode("utf-8")).hexdigest()
        return cls(
            plan=plan,
            recovery_digest=recovery_digest,
            policy_version=policy_version,
            previous_digest=previous_digest,
            digest=digest,
        )

    def verify(self) -> bool:
        payload = self.canonical_payload(
            self.plan,
            self.recovery_digest,
            self.policy_version,
            self.previous_digest,
        )
        return sha256(payload.encode("utf-8")).hexdigest() == self.digest

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
