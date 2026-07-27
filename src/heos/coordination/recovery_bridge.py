from __future__ import annotations

from dataclasses import dataclass

from heos.continuity import RecoveryMode, RecoverySnapshot

from .audit import CoordinationAuditTrail


@dataclass(frozen=True, slots=True)
class CoordinationRecoveryBridge:
    """Build a conservative recovery snapshot from coordination audit history."""

    recovery_ttl: int = 300

    def __post_init__(self) -> None:
        if self.recovery_ttl <= 0:
            raise ValueError("recovery_ttl must be positive")

    def build_snapshot(
        self,
        trail: CoordinationAuditTrail,
        *,
        now: int,
    ) -> RecoverySnapshot:
        if now < 0:
            raise ValueError("now must be non-negative")

        if not trail.verify_chain():
            raise ValueError("coordination audit chain is invalid")

        records = trail.records()

        if not records:
            return RecoverySnapshot(
                incident_id="coordination-restart-empty",
                mode=RecoveryMode.SAFE_STOP,
                severity=100,
                fallback_strategy=None,
                valid_until=now + self.recovery_ttl,
                metadata={
                    "source": "coordination_audit",
                    "reason": "no_authorization_history",
                },
            )

        latest = records[-1]

        if latest.release_status == "rejected":
            mode = RecoveryMode.SAFE_STOP
            severity = 100
            reason = "last_release_rejected"
        elif latest.release_status == "held":
            mode = RecoveryMode.HOLD
            severity = 80
            reason = "last_release_held"
        elif latest.release_status == "released":
            mode = RecoveryMode.HOLD
            severity = 60
            reason = "historical_release_requires_reauthorization"
        else:
            mode = RecoveryMode.SAFE_STOP
            severity = 100
            reason = "unknown_release_status"

        return RecoverySnapshot(
            incident_id=f"coordination-restart-{latest.release_id}",
            mode=mode,
            severity=severity,
            fallback_strategy=None,
            valid_until=now + self.recovery_ttl,
            metadata={
                "source": "coordination_audit",
                "reason": reason,
                "cycle_id": latest.cycle_id,
                "release_id": latest.release_id,
                "release_status": latest.release_status,
                "audit_digest": latest.digest,
                "requested_mode": latest.requested_mode,
                "effective_mode": latest.effective_mode,
            },
        )