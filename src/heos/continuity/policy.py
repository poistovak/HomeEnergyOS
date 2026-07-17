from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from .models import (
    ContinuityPlan,
    ContinuityStatus,
    RecoveryMode,
    RecoverySnapshot,
)


@dataclass(frozen=True, slots=True)
class ContinuityPolicy:
    version: str = "25.0.0"
    automatic_threshold: int = 45
    approval_threshold: int = 75
    automatic_attempts: int = 3
    approved_attempts: int = 1
    cooldown_seconds: int = 30
    plan_ttl: int = 300

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        if not 0 <= self.automatic_threshold <= self.approval_threshold <= 100:
            raise ValueError("invalid continuity thresholds")
        if self.automatic_attempts < 0 or self.approved_attempts < 0:
            raise ValueError("attempt counts must be non-negative")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be non-negative")
        if self.plan_ttl <= 0:
            raise ValueError("plan_ttl must be positive")

    def build_plan(
        self,
        recovery: RecoverySnapshot,
        *,
        now: int,
    ) -> ContinuityPlan:
        if now < 0:
            raise ValueError("now must be non-negative")

        expired = now > recovery.valid_until
        status: ContinuityStatus
        action: str
        attempts: int
        approval_required: bool
        reasons: tuple[str, ...]

        if expired:
            status = ContinuityStatus.BLOCKED
            action = "reject_expired_recovery"
            attempts = 0
            approval_required = False
            reasons = ("recovery decision expired",)
        elif recovery.mode is RecoveryMode.SAFE_STOP:
            status = ContinuityStatus.BLOCKED
            action = "maintain_safe_stop"
            attempts = 0
            approval_required = False
            reasons = ("safe stop is authoritative",)
        elif recovery.mode is RecoveryMode.HOLD:
            status = ContinuityStatus.APPROVAL_REQUIRED
            action = "maintain_hold"
            attempts = self.approved_attempts
            approval_required = True
            reasons = ("recovery mode requires approval",)
        elif recovery.severity >= self.approval_threshold:
            status = ContinuityStatus.APPROVAL_REQUIRED
            action = recovery.fallback_strategy or "conservative_recovery"
            attempts = self.approved_attempts
            approval_required = True
            reasons = ("severity exceeds approval threshold",)
        elif recovery.severity <= self.automatic_threshold:
            status = ContinuityStatus.AUTOMATIC
            action = recovery.fallback_strategy or "bounded_continue"
            attempts = self.automatic_attempts
            approval_required = False
            reasons = ("bounded automatic continuity",)
        else:
            status = ContinuityStatus.APPROVAL_REQUIRED
            action = recovery.fallback_strategy or "bounded_degradation"
            attempts = self.approved_attempts
            approval_required = True
            reasons = ("severity requires operator approval",)

        deadline = min(recovery.valid_until, now + self.plan_ttl)
        payload = {
            "incident_id": recovery.incident_id,
            "status": status.value,
            "action": action,
            "attempts": attempts,
            "cooldown_seconds": self.cooldown_seconds,
            "deadline": deadline,
            "approval_required": approval_required,
            "policy_version": self.version,
        }
        plan_id = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:24]

        return ContinuityPlan(
            plan_id=plan_id,
            incident_id=recovery.incident_id,
            status=status,
            action=action,
            max_attempts=attempts,
            cooldown_seconds=self.cooldown_seconds,
            deadline=deadline,
            approval_token_required=approval_required,
            reasons=reasons,
        )
