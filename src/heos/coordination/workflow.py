from typing import ClassVar

from heos.coordination.state import CoordinationState


class Workflow:
    """Defines valid state transitions for one coordination cycle."""

    _TRANSITIONS: ClassVar[dict[CoordinationState, CoordinationState]] = {
        CoordinationState.CREATED: CoordinationState.PLANNING,
        CoordinationState.PLANNING: CoordinationState.ARBITRATING,
        CoordinationState.ARBITRATING: CoordinationState.VALIDATING,
        CoordinationState.VALIDATING: CoordinationState.EXECUTING,
        CoordinationState.EXECUTING: CoordinationState.VERIFYING,
        CoordinationState.VERIFYING: CoordinationState.COMPLETED,
    }

    _TERMINAL_STATES = frozenset(
        {
            CoordinationState.COMPLETED,
            CoordinationState.FAILED,
            CoordinationState.CANCELLED,
            CoordinationState.TIMED_OUT,
        }
    )

    @classmethod
    def next_state(cls, state: CoordinationState) -> CoordinationState:
        """Return the next valid workflow state."""
        return cls._TRANSITIONS[state]

    @classmethod
    def is_terminal(cls, state: CoordinationState) -> bool:
        """Return whether the state ends the coordination cycle."""
        return state in cls._TERMINAL_STATES

    @classmethod
    def allowed_next(
        cls,
        state: CoordinationState,
    ) -> CoordinationState | None:
        """Return the allowed next state, or None for a terminal state."""
        return cls._TRANSITIONS.get(state)

    @classmethod
    def can_transition(
        cls,
        current: CoordinationState,
        target: CoordinationState,
    ) -> bool:
        """Return whether a direct transition is allowed."""
        return cls.allowed_next(current) == target