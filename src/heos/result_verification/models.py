from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Tuple


class VerificationStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class VerificationAction(str, Enum):
    ACCEPT = "accept"
    RETRY = "retry"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class ResultExpectation:
    command_id: str
    target: str
    expected_value: float
    absolute_tolerance: float = 0.0
    relative_tolerance: float = 0.0
    deadline: int = 0
    stability_samples: int = 1
    minimum_samples: int = 1
    rollback_supported: bool = False

    def __post_init__(self) -> None:
        if not self.command_id.strip() or not self.target.strip():
            raise ValueError("command_id and target must not be empty")
        if self.absolute_tolerance < 0 or self.relative_tolerance < 0:
            raise ValueError("tolerances must be non-negative")
        if self.deadline < 0:
            raise ValueError("deadline must be non-negative")
        if self.stability_samples < 1 or self.minimum_samples < 1:
            raise ValueError("sample counts must be at least one")

    @property
    def effective_tolerance(self) -> float:
        return max(
            self.absolute_tolerance,
            abs(self.expected_value) * self.relative_tolerance,
        )


@dataclass(frozen=True, slots=True)
class Observation:
    target: str
    value: float
    observed_at: int
    source: str = "unknown"
    quality: float = 1.0

    def __post_init__(self) -> None:
        if not self.target.strip() or not self.source.strip():
            raise ValueError("target and source must not be empty")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError("quality must be between zero and one")


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    verification_id: str
    command_id: str
    target: str
    status: VerificationStatus
    action: VerificationAction
    expected_value: float
    observed_value: float | None
    absolute_error: float | None
    relative_error: float | None
    stable_samples: int
    evidence_count: int
    attempts_used: int
    reasons: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.verification_id.strip() or not self.command_id.strip():
            raise ValueError("verification identifiers must not be empty")
        if self.stable_samples < 0 or self.evidence_count < 0 or self.attempts_used < 0:
            raise ValueError("verification counters must be non-negative")
        if not self.reasons:
            raise ValueError("reasons must not be empty")
        if self.status is VerificationStatus.SUCCESS and self.action is not VerificationAction.ACCEPT:
            raise ValueError("successful verification must be accepted")

    @classmethod
    def create(
        cls,
        *,
        command_id: str,
        target: str,
        status: VerificationStatus,
        action: VerificationAction,
        expected_value: float,
        observed_value: float | None,
        absolute_error: float | None,
        relative_error: float | None,
        stable_samples: int,
        evidence_count: int,
        attempts_used: int,
        reasons: Tuple[str, ...],
        policy_version: str,
    ) -> "VerificationDecision":
        payload = {
            "command_id": command_id,
            "target": target,
            "status": status.value,
            "action": action.value,
            "expected_value": expected_value,
            "observed_value": observed_value,
            "absolute_error": absolute_error,
            "relative_error": relative_error,
            "stable_samples": stable_samples,
            "evidence_count": evidence_count,
            "attempts_used": attempts_used,
            "reasons": reasons,
            "policy_version": policy_version,
        }
        digest = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()
        return cls(
            verification_id="vrf-" + digest[:20],
            command_id=command_id,
            target=target,
            status=status,
            action=action,
            expected_value=expected_value,
            observed_value=observed_value,
            absolute_error=absolute_error,
            relative_error=relative_error,
            stable_samples=stable_samples,
            evidence_count=evidence_count,
            attempts_used=attempts_used,
            reasons=reasons,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)
