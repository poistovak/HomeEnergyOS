from __future__ import annotations

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

        if result.release.status is ReleaseStatus.RELEASED:
            context.state = CoordinationState.EXECUTING.value
        elif result.release.status is ReleaseStatus.REJECTED:
            context.state = CoordinationState.FAILED.value

        return result