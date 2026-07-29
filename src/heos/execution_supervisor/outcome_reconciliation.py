from __future__ import annotations

from dataclasses import dataclass

from heos.continuity.models import RecoveryMode, RecoverySnapshot
from heos.outcome_verifier.models import OutcomeCertificate, OutcomeStatus


@dataclass(frozen=True, slots=True)
class ExecutionOutcomeReconciler:
    """Translate verified execution outcome into conservative recovery state."""

    recovery_ttl: int = 300

    def __post_init__(self) -> None:
        if self.recovery_ttl <= 0:
            raise ValueError("recovery_ttl must be positive")

    def reconcile(
        self,
        certificate: OutcomeCertificate,
        *,
        now: int,
    ) -> RecoverySnapshot:
        if now < 0:
            raise ValueError("now must be non-negative")

        if not certificate.verify():
            raise ValueError("outcome certificate is invalid")

        result = certificate.result

        if result.status is OutcomeStatus.VERIFIED:
            mode = RecoveryMode.HOLD
            severity = 20
            reason = "execution_already_verified_no_replay"
        elif result.status is OutcomeStatus.DEGRADED:
            mode = RecoveryMode.HOLD
            severity = 60
            reason = "degraded_outcome_requires_review"
        elif result.status is OutcomeStatus.FAILED:
            mode = RecoveryMode.SAFE_STOP
            severity = 90
            reason = "execution_outcome_failed"
        else:
            mode = RecoveryMode.HOLD
            severity = 80
            reason = "execution_outcome_inconclusive_no_replay"

        return RecoverySnapshot(
            incident_id=f"execution-outcome-{result.result_id}",
            mode=mode,
            severity=severity,
            fallback_strategy=None,
            valid_until=now + self.recovery_ttl,
            metadata={
                "source": "outcome_verifier",
                "reason": reason,
                "outcome_certificate_digest": certificate.digest,
                "result_id": result.result_id,
                "command_id": result.command_id,
                "incident_id": result.incident_id,
                "outcome_status": result.status.value,
                "outcome_policy_version": certificate.policy_version,
                "expectation_digest": certificate.expectation_digest,
                "evidence_digest": certificate.evidence_digest,
            },
        )