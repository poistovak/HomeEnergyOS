import pytest

from heos.coordination.state import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_states_are_recognized(state):
    assert Workflow.is_terminal(state) is True


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
def test_active_states_are_not_terminal(state):
    assert Workflow.is_terminal(state) is False


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ],
)
def test_allowed_next_returns_expected_state(current, expected):
    assert Workflow.allowed_next(current) == expected


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_states_have_no_allowed_next(state):
    assert Workflow.allowed_next(state) is None


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.ARBITRATING),
        (CoordinationState.PLANNING, CoordinationState.VALIDATING),
        (CoordinationState.ARBITRATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.COMPLETED),
        (CoordinationState.COMPLETED, CoordinationState.CREATED),
    ],
)
def test_invalid_direct_transitions_are_rejected(current, target):
    assert Workflow.can_transition(current, target) is False
