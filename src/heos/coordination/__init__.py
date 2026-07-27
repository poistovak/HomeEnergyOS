from __future__ import annotations

from dataclasses import replace

from heos.coordination.audit import (
    CoordinationAuditRecord,
    CoordinationAuditTrail,
)
from heos.coordination.autonomy_controller import (
    AutonomyController,
    AutonomyControlResult,
)
from heos.coordination.context import CoordinationContext
from heos.coordination.state import CoordinationState
from heos.coordination.workflow import Workflow
from heos.release_gate import OperationalRequest, ReleaseStatus


class CoordinationCoordinator:
    """Coordinates one HEOS decision cycle."""

    def __init__(
        self,
        *,
        audit_trail: CoordinationAuditTrail | None = None,
    ) -> None:
        self.audit_trail = (
            audit_trail
            if audit_trail is not None
            else CoordinationAuditTrail()
        )

    def start(
        self,
        context: CoordinationContext,
    ) -> CoordinationContext:
        context.state = CoordinationState.PLANNING.value
        return context

    def advance(
        self,
        context: CoordinationContext,
    ) -> CoordinationContext:
        current = CoordinationState(context.state)
        context.state = Workflow.next_state(current).value
        return context

    def authorize_execution(
        self,
        context: CoordinationContext,
        *,
        controller: AutonomyController,
        request: OperationalRequest,
    ) -> AutonomyControlResult:
        """Evaluate autonomy authority before entering execution."""
        current = CoordinationState(context.state)

        if current is not CoordinationState.VALIDATING:
            raise ValueError(
                "execution authorization requires VALIDATING state"
            )

        result = controller.evaluate(request)

        context.metadata["autonomy_requested_mode"] = (
            result.mode_result.requested_mode.value
        )
        context.metadata["autonomy_effective_mode"] = (
            result.mode_result.effective_mode.value
        )
        context.metadata["autonomy_downgraded"] = result.downgraded
        context.metadata["release_status"] = result.release.status.value
        context.metadata["release_id"] = result.release.release_id

        self.audit_trail.append(
            CoordinationAuditRecord(
                cycle_id=context.cycle_id,
                requested_mode=result.mode_result.requested_mode.value,
                effective_mode=result.mode_result.effective_mode.value,
                downgraded=result.downgraded,
                operator_approved=request.operator_approved,
                autonomy_authorized=request.autonomy_authorized,
                release_status=result.release.status.value,
                release_id=result.release.release_id,
                approval_resume=bool(
                    context.metadata.get(
                        "approval_resume",
                        False,
                    )
                ),
            )
        )

        if result.release.status is ReleaseStatus.RELEASED:
            context.state = CoordinationState.EXECUTING.value
        elif result.release.status is ReleaseStatus.REJECTED:
            context.state = CoordinationState.FAILED.value

        return result

    def resume_with_approval(
        self,
        context: CoordinationContext,
        *,
        controller: AutonomyController,
        request: OperationalRequest,
        operator_approved: bool | None = None,
        autonomy_authorized: bool | None = None,
    ) -> AutonomyControlResult:
        """Re-evaluate a held release after approval state changes."""
        current = CoordinationState(context.state)

        if current is not CoordinationState.VALIDATING:
            raise ValueError(
                "approval resume requires VALIDATING state"
            )

        updated_request = replace(
            request,
            operator_approved=(
                request.operator_approved
                if operator_approved is None
                else operator_approved
            ),
            autonomy_authorized=(
                request.autonomy_authorized
                if autonomy_authorized is None
                else autonomy_authorized
            ),
        )

        context.metadata["approval_resume"] = True

        return self.authorize_execution(
            context,
            controller=controller,
            request=updated_request,
        )