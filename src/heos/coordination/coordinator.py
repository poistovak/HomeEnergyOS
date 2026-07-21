from heos.coordination.context import CoordinationContext
from heos.coordination.state import CoordinationState
from heos.coordination.workflow import Workflow


class CoordinationCoordinator:
    """Coordinates one HEOS decision cycle."""

    def start(self, context: CoordinationContext) -> CoordinationContext:
        context.state = CoordinationState.PLANNING.value
        return context

    def advance(self, context: CoordinationContext) -> CoordinationContext:
        current = CoordinationState(context.state)
        context.state = Workflow.next_state(current).value
        return context
