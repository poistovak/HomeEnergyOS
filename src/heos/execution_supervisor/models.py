from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Tuple


class ExecutionStatus(str, Enum):
    READY = "ready"
    WAITING_APPROVAL = "waiting_approval"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class ContinuityDirective:
    plan_id: str
    incident_id: str
    status: str
    action: str
    max_attempts: int
    cooldown_seconds: int
    deadline: int
    approval_token_required: bool
    source_digest: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.incident_id.strip():
            raise ValueError("plan_id and incident_id must not be empty")
        if not self.action.strip() or not self.source_digest.strip():
            raise ValueError("action and source_digest must not be empty")
        if self.max_attempts < 0 or self.cooldown_seconds < 0 or self.deadline < 0:
            raise ValueError("numeric limits must be non-negative")


@dataclass(frozen=True, slots=True)
class ApprovalToken:
    token_id: str
    plan_id: str
    approved_action: str
    valid_until: int
    issuer: str

    def __post_init__(self) -> None:
        if not all((self.token_id.strip(), self.plan_id.strip(), self.approved_action.strip(), self.issuer.strip())):
            raise ValueError("approval token fields must not be empty")
        if self.valid_until < 0:
            raise ValueError("valid_until must be non-negative")


@dataclass(frozen=True, slots=True)
class ExecutionCommand:
    command_id: str
    plan_id: str
    incident_id: str
    status: ExecutionStatus
    action: str
    attempt_limit: int
    cooldown_seconds: int
    valid_until: int
    reasons: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.action.strip():
            raise ValueError("command_id and action must not be empty")
        if self.attempt_limit < 0 or self.cooldown_seconds < 0 or self.valid_until < 0:
            raise ValueError("command limits must be non-negative")
        if not self.reasons:
            raise ValueError("reasons must not be empty")
        if self.status is not ExecutionStatus.READY and self.attempt_limit != 0:
            raise ValueError("non-ready command must have zero attempts")


@dataclass(frozen=True, slots=True)
class ExecutionCertificate:
    command: ExecutionCommand
    directive_digest: str
    policy_version: str
    previous_digest: str | None
    digest: str

    @staticmethod
    def canonical_payload(command: ExecutionCommand, directive_digest: str, policy_version: str, previous_digest: str | None) -> str:
        return json.dumps(
            {
                "command": asdict(command),
                "directive_digest": directive_digest,
                "policy_version": policy_version,
                "previous_digest": previous_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @classmethod
    def issue(cls, *, command: ExecutionCommand, directive_digest: str, policy_version: str, previous_digest: str | None = None) -> "ExecutionCertificate":
        payload = cls.canonical_payload(command, directive_digest, policy_version, previous_digest)
        return cls(command, directive_digest, policy_version, previous_digest, sha256(payload.encode()).hexdigest())

    def verify(self) -> bool:
        payload = self.canonical_payload(self.command, self.directive_digest, self.policy_version, self.previous_digest)
        return sha256(payload.encode()).hexdigest() == self.digest

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)
