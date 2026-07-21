import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.CREATED,
        CoordinationState.PLANNING,
        CoordinationState.ARBITRATING,
        CoordinationState.VALIDATING,
        CoordinationState.EXECUTING,
        CoordinationState.VERIFYING,
    ],
)
def test_allowed_next_is_consistent(state):
    nxt = Workflow.allowed_next(state)
    assert nxt == Workflow.next_state(state)
    assert Workflow.can_transition(state, nxt)


@pytest.mark.parametrize(
    "terminal",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_state_properties(terminal):
    assert Workflow.is_terminal(terminal)
    assert Workflow.allowed_next(terminal) is None
    assert not Workflow.can_transition(terminal, terminal)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.COMPLETED),
        (CoordinationState.PLANNING, CoordinationState.VERIFYING),
        (CoordinationState.ARBITRATING, CoordinationState.COMPLETED),
        (CoordinationState.VALIDATING, CoordinationState.CREATED),
        (CoordinationState.EXECUTING, CoordinationState.PLANNING),
        (CoordinationState.VERIFYING, CoordinationState.CREATED),
    ],
)
def test_invalid_shortcuts(current, target):
    assert Workflow.can_transition(current, target) is False