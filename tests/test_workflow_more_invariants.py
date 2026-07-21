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
def test_allowed_next_matches_transition_table(state, expected):
    assert Workflow.allowed_next(state) == expected


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.CREATED,
        CoordinationState.PLANNING,
        CoordinationState.ARBITRATING,
        CoordinationState.VALIDATING,
        CoordinationState.EXECUTING,
        CoordinationState.VERIFYING,
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_state_cannot_transition_to_itself(state):
    assert not Workflow.can_transition(state, state)


@pytest.mark.parametrize(
    ("terminal", "target"),
    [
        (CoordinationState.COMPLETED, CoordinationState.PLANNING),
        (CoordinationState.FAILED, CoordinationState.PLANNING),
        (CoordinationState.CANCELLED, CoordinationState.PLANNING),
        (CoordinationState.TIMED_OUT, CoordinationState.PLANNING),
        (CoordinationState.COMPLETED, CoordinationState.CREATED),
        (CoordinationState.FAILED, CoordinationState.CREATED),
        (CoordinationState.CANCELLED, CoordinationState.CREATED),
        (CoordinationState.TIMED_OUT, CoordinationState.CREATED),
    ],
)
def test_terminal_states_have_no_outgoing_transition(terminal, target):
    assert not Workflow.can_transition(terminal, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.PLANNING, CoordinationState.CREATED),
        (CoordinationState.ARBITRATING, CoordinationState.CREATED),
        (CoordinationState.ARBITRATING, CoordinationState.PLANNING),
        (CoordinationState.VALIDATING, CoordinationState.CREATED),
        (CoordinationState.VALIDATING, CoordinationState.PLANNING),
        (CoordinationState.VALIDATING, CoordinationState.ARBITRATING),
        (CoordinationState.EXECUTING, CoordinationState.CREATED),
        (CoordinationState.EXECUTING, CoordinationState.PLANNING),
        (CoordinationState.EXECUTING, CoordinationState.ARBITRATING),
        (CoordinationState.EXECUTING, CoordinationState.VALIDATING),
        (CoordinationState.VERIFYING, CoordinationState.CREATED),
        (CoordinationState.VERIFYING, CoordinationState.PLANNING),
        (CoordinationState.VERIFYING, CoordinationState.ARBITRATING),
        (CoordinationState.VERIFYING, CoordinationState.VALIDATING),
        (CoordinationState.VERIFYING, CoordinationState.EXECUTING),
    ],
)
def test_backward_transitions_are_forbidden(current, target):
    assert not Workflow.can_transition(current, target)


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
def test_next_state_equals_allowed_next(state, expected):
    assert Workflow.next_state(state) == expected
    assert Workflow.next_state(state) == Workflow.allowed_next(state)