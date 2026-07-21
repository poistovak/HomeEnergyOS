import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ],
)
def test_transition_roundtrip(state, expected):
    assert Workflow.allowed_next(state) == expected
    assert Workflow.next_state(state) == expected
    assert Workflow.can_transition(state, expected)


@pytest.mark.parametrize(
    "terminal",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_invariants(terminal):
    assert Workflow.is_terminal(terminal)
    assert Workflow.allowed_next(terminal) is None


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
def test_active_states_have_successor(state):
    assert Workflow.allowed_next(state) is not None