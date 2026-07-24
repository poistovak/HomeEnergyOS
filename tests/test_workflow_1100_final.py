import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow

TRANSITIONS = (
    (CoordinationState.CREATED, CoordinationState.PLANNING),
    (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
    (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
    (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
    (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
    (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
)


@pytest.mark.parametrize(("src", "dst"), TRANSITIONS)
def test_next_state_matches_expected(src, dst):
    assert Workflow.next_state(src) == dst


@pytest.mark.parametrize(("src", "dst"), TRANSITIONS)
def test_transition_is_allowed(src, dst):
    assert Workflow.can_transition(src, dst)


@pytest.mark.parametrize(("src", "dst"), TRANSITIONS)
def test_allowed_next_matches_expected(src, dst):
    assert Workflow.allowed_next(src) == dst


@pytest.mark.parametrize(
    "terminal",
    (
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ),
)
def test_terminal_contract(terminal):
    assert Workflow.is_terminal(terminal)
    assert Workflow.allowed_next(terminal) is None