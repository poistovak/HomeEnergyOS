from __future__ import annotations

from dataclasses import dataclass

from heos.continuity.models import RecoveryMode, RecoverySnapshot

from .ledger import ExecutionLedger
from .models import ExecutionStatus


@dataclass(frozen=True, slots=True)
class ExecutionRestartReconciler:
    """Convert persisted execution history into conservative recovery state."""

    recovery_ttl: int = 300

    def __post_init__(self) -> None:
        if self.recovery_ttl <= 0:
            raise ValueError("recovery_ttl must be positive")

    def reconcile(
        self,
        ledger: ExecutionLedger,
        *,
        now: int,
    ) -> RecoverySnapshot:
        if now < 0:
            raise ValueError("now must be non-negative")

        if not ledger.verify_chain():
            raise ValueError("execution ledger chain is invalid")

        entries = ledger.entries()

        if not entries:
            return RecoverySnapshot(
                incident_id="execution-restart-empty",
                mode=RecoveryMode.SAFE_STOP,
                severity=100,
                fallback_strategy=None,
                valid_until=now + self.recovery_ttl,
                metadata={
                    "source": "execution_ledger",
                    "reason": "no_execution_history",
                },
            )

        latest = entries[-1]
        command = latest.command

        if command.status is ExecutionStatus.READY:
            if now > command.valid_until:
                mode = RecoveryMode.SAFE_STOP
                severity = 100
                reason = "ready_command_expired_during_restart"
            else:
                mode = RecoveryMode.HOLD
                severity = 80
                reason = "ready_command_requires_reauthorization"

        elif command.status is ExecutionStatus.WAITING_APPROVAL:
            mode = RecoveryMode.HOLD
            severity = 80
            reason = "approval_must_be_revalidated_after_restart"

        elif command.status is ExecutionStatus.EXPIRED:
            mode = RecoveryMode.SAFE_STOP
            severity = 100
            reason = "last_execution_expired"

        else:
            mode = RecoveryMode.SAFE_STOP
            severity = 100
            reason = "last_execution_rejected"

        return RecoverySnapshot(
            incident_id=f"execution-restart-{command.command_id}",
            mode=mode,
            severity=severity,
            fallback_strategy=None,
            valid_until=now + self.recovery_ttl,
            metadata={
                "source": "execution_ledger",
                "reason": reason,
                "execution_certificate_digest": latest.digest,
                "command_id": command.command_id,
                "plan_id": command.plan_id,
                "execution_status": command.status.value,
                "directive_digest": latest.directive_digest,
                "execution_policy_version": latest.policy_version,
            },
        )