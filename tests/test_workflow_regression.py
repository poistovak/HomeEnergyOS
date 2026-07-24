import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow

TRANSITIONS = [
    (CoordinationState.CREATED, CoordinationState.PLANNING),
    (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
    (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
    (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
    (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
    (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
]


@pytest.mark.parametrize(("current", "expected"), TRANSITIONS)
def test_transition_table_is_consistent(current, expected):
    assert Workflow.next_state(current) == expected
    assert Workflow.allowed_next(current) == expected
    assert Workflow.can_transition(current, expected)


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_states_have_no_successor(state):
    assert Workflow.allowed_next(state) is None
    assert Workflow.is_terminal(state)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.VALIDATING),
        (CoordinationState.CREATED, CoordinationState.COMPLETED),
        (CoordinationState.PLANNING, CoordinationState.EXECUTING),
        (CoordinationState.PLANNING, CoordinationState.VERIFYING),
        (CoordinationState.ARBITRATING, CoordinationState.COMPLETED),
        (CoordinationState.VALIDATING, CoordinationState.COMPLETED),
        (CoordinationState.EXECUTING, CoordinationState.CREATED),
        (CoordinationState.VERIFYING, CoordinationState.CREATED),
        (CoordinationState.COMPLETED, CoordinationState.PLANNING),
        (CoordinationState.FAILED, CoordinationState.CREATED),
        (CoordinationState.CANCELLED, CoordinationState.CREATED),
        (CoordinationState.TIMED_OUT, CoordinationState.CREATED),
    ],
)
def test_invalid_transitions_are_rejected(current, target):
    assert Workflow.can_transition(current, target) is False


@pytest.mark.parametrize("state", [t[0] for t in TRANSITIONS])
def test_next_state_equals_allowed_next(state):
    assert Workflow.next_state(state) == Workflow.allowed_next(state)


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
    assert not Workflow.is_terminal(state)