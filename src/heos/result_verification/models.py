from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class VerificationStatus(StrEnum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    TIMEOUT = "TIMEOUT"


class VerificationAction(StrEnum):
    ACCEPT = "ACCEPT"
    RETRY = "RETRY"
    ROLLBACK = "ROLLBACK"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True, slots=True)
class ResultExpectation:
    command_id: str
    target: str
    expected_value: float
    absolute_tolerance: float
    relative_tolerance: float
    deadline: int
    stability_samples: int
    minimum_samples: int
    rollback_supported: bool

    @property
    def effective_tolerance(self) -> float:
        relative = abs(self.expected_value) * self.relative_tolerance
        return max(
            self.absolute_tolerance,
            relative,
        )

    def __post_init__(self) -> None:
        if not self.command_id.strip():
            raise ValueError("command_id must not be empty")

        if not self.target.strip():
            raise ValueError("target must not be empty")

        if self.absolute_tolerance < 0:
            raise ValueError(
                "absolute_tolerance must be non-negative"
            )

        if self.relative_tolerance < 0:
            raise ValueError(
                "relative_tolerance must be non-negative"
            )

        if self.deadline < 0:
            raise ValueError(
                "deadline must be non-negative"
            )

        if self.stability_samples < 1:
            raise ValueError(
                "stability_samples must be positive"
            )

        if self.minimum_samples < 1:
            raise ValueError(
                "minimum_samples must be positive"
            )


@dataclass(frozen=True, slots=True)
class Observation:
    target: str
    value: float
    observed_at: int | datetime
    source: str
    quality: float = 1.0

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError("target must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not math.isfinite(self.value):
            raise ValueError("value must be finite")

        if isinstance(self.observed_at, datetime) and self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        if not 0.0 <= self.quality <= 1.0:
            raise ValueError(
                "quality must be between 0 and 1"
            )


@dataclass(frozen=True, slots=True)
class VerificationDecision:
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
    reasons: tuple[str, ...]
    policy_version: str

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
        reasons: tuple[str, ...],
        policy_version: str,
    ) -> VerificationDecision:
        return cls(
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
            policy_version=policy_version,
        )

    @property
    def verification_id(self) -> str:
        return (
            f"{self.command_id}:"
            f"{self.status.value}:"
            f"{self.action.value}"
        )

    def to_json(self) -> str:
        return json.dumps(
            {
                "command_id": self.command_id,
                "target": self.target,
                "status": self.status.value.lower(),
                "action": self.action.value.lower(),
                "expected_value": self.expected_value,
                "observed_value": self.observed_value,
                "absolute_error": self.absolute_error,
                "relative_error": self.relative_error,
                "stable_samples": self.stable_samples,
                "evidence_count": self.evidence_count,
                "attempts_used": self.attempts_used,
                "reasons": list(self.reasons),
                "policy_version": self.policy_version,
            },
            separators=(",", ":"),
            sort_keys=True,
        )

    def __post_init__(self) -> None:
        if not self.command_id.strip():
            raise ValueError("command_id must not be empty")

        if not self.target.strip():
            raise ValueError("target must not be empty")

        if self.absolute_error is not None and self.absolute_error < 0:
            raise ValueError(
                "absolute_error must be non-negative"
            )

        if self.relative_error is not None and self.relative_error < 0:
            raise ValueError(
                "relative_error must be non-negative"
            )

        if self.stable_samples < 0:
            raise ValueError(
                "stable_samples must be non-negative"
            )

        if self.evidence_count < 0:
            raise ValueError(
                "evidence_count must be non-negative"
            )

        if self.attempts_used < 0:
            raise ValueError(
                "attempts_used must be non-negative"
            )