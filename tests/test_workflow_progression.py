import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


ACTIVE = (
    CoordinationState.CREATED,
    CoordinationState.PLANNING,
    CoordinationState.ARBITRATING,
    CoordinationState.VALIDATING,
    CoordinationState.EXECUTING,
    CoordinationState.VERIFYING,
)


@pytest.mark.parametrize("state", ACTIVE)
def test_next_state_matches_allowed_next(state):
    assert Workflow.next_state(state) == Workflow.allowed_next(state)


@pytest.mark.parametrize("state", ACTIVE)
def test_state_progresses_forward(state):
    nxt = Workflow.next_state(state)
    assert Workflow.can_transition(state, nxt)


@pytest.mark.parametrize(
    "terminal",
    (
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ),
)
def test_terminal_states_raise_key_error(terminal):
    with pytest.raises(KeyError):
        Workflow.next_state(terminal)

    assert Workflow.allowed_next(terminal) is None
    assert Workflow.is_terminal(terminal)