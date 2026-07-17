from __future__ import annotations

from dataclasses import dataclass

from .models import VerificationAction, VerificationStatus


@dataclass(frozen=True, slots=True)
class ResultVerificationPolicy:
    version: str = "28.0.0"
    retry_limit: int = 2
    partial_multiplier: float = 2.0
    rollback_after_failure: bool = True
    minimum_quality: float = 0.5

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        if self.retry_limit < 0:
            raise ValueError("retry_limit must be non-negative")
        if self.partial_multiplier < 1.0:
            raise ValueError("partial_multiplier must be at least one")
        if not 0.0 <= self.minimum_quality <= 1.0:
            raise ValueError("minimum_quality must be between zero and one")

    def choose_action(
        self,
        status: VerificationStatus,
        *,
        attempts_used: int,
        rollback_supported: bool,
    ) -> VerificationAction:
        if status is VerificationStatus.SUCCESS:
            return VerificationAction.ACCEPT
        if status in (VerificationStatus.PARTIAL, VerificationStatus.UNKNOWN):
            if attempts_used < self.retry_limit:
                return VerificationAction.RETRY
            return VerificationAction.ESCALATE
        if status is VerificationStatus.TIMEOUT:
            if attempts_used < self.retry_limit:
                return VerificationAction.RETRY
            if rollback_supported and self.rollback_after_failure:
                return VerificationAction.ROLLBACK
            return VerificationAction.ESCALATE
        if rollback_supported and self.rollback_after_failure:
            return VerificationAction.ROLLBACK
        if attempts_used < self.retry_limit:
            return VerificationAction.RETRY
        return VerificationAction.ESCALATE
