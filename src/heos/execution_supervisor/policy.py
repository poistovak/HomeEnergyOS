from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .models import ApprovalToken, ContinuityDirective, ExecutionCommand, ExecutionStatus


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    version: str = "26.0.0"
    maximum_attempts: int = 5

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("version must not be empty")
        if self.maximum_attempts < 1:
            raise ValueError("maximum_attempts must be positive")

    def build_command(self, directive: ContinuityDirective, *, now: int, approval: ApprovalToken | None = None) -> ExecutionCommand:
        if now < 0:
            raise ValueError("now must be non-negative")
        status = ExecutionStatus.READY
        reasons: list[str] = []
        attempts = min(directive.max_attempts, self.maximum_attempts)

        if now > directive.deadline:
            status, attempts = ExecutionStatus.EXPIRED, 0
            reasons.append("continuity directive expired")
        elif directive.status == "blocked":
            status, attempts = ExecutionStatus.REJECTED, 0
            reasons.append("continuity governor blocked execution")
        elif directive.approval_token_required:
            error = self._approval_error(directive, approval, now)
            if error:
                status, attempts = ExecutionStatus.WAITING_APPROVAL, 0
                reasons.append(error)
            else:
                reasons.append("valid approval token accepted")
        else:
            reasons.append("automatic continuity authorized")

        if status is ExecutionStatus.READY and attempts == 0:
            status = ExecutionStatus.REJECTED
            reasons.append("no execution attempts authorized")

        payload = {
            "directive": asdict(directive),
            "status": status.value,
            "attempts": attempts,
            "policy_version": self.version,
        }
        command_id = "cmd-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:20]
        return ExecutionCommand(
            command_id=command_id,
            plan_id=directive.plan_id,
            incident_id=directive.incident_id,
            status=status,
            action=directive.action if status is ExecutionStatus.READY else "no_op",
            attempt_limit=attempts,
            cooldown_seconds=directive.cooldown_seconds,
            valid_until=directive.deadline,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _approval_error(directive: ContinuityDirective, approval: ApprovalToken | None, now: int) -> str | None:
        if approval is None:
            return "approval token required"
        if approval.valid_until < now:
            return "approval token expired"
        if approval.plan_id != directive.plan_id:
            return "approval token plan mismatch"
        if approval.approved_action != directive.action:
            return "approval token action mismatch"
        return None
