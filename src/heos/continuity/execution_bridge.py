from __future__ import annotations

from dataclasses import dataclass

from heos.execution_supervisor import ContinuityDirective

from .models import ContinuityCertificate


@dataclass(frozen=True, slots=True)
class ContinuityExecutionBridge:
    """Convert a certified continuity plan into an execution directive."""

    source: str = "continuity"

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")

    def build(
        self,
        certificate: ContinuityCertificate,
    ) -> ContinuityDirective:
        if not certificate.verify():
            raise ValueError("continuity certificate is invalid")

        plan = certificate.plan

        return ContinuityDirective(
            plan_id=plan.plan_id,
            incident_id=plan.incident_id,
            status=plan.status.value,
            action=plan.action,
            max_attempts=plan.max_attempts,
            cooldown_seconds=plan.cooldown_seconds,
            deadline=plan.deadline,
            approval_token_required=plan.approval_token_required,
            source_digest=certificate.digest,
            metadata={
                "source": self.source,
                "continuity_policy_version": certificate.policy_version,
                "continuity_digest": certificate.digest,
                "recovery_digest": certificate.recovery_digest,
            },
        )