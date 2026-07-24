import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow

ACTIVE_TRANSITIONS = [
    (CoordinationState.CREATED, CoordinationState.PLANNING),
    (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
    (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
    (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
    (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
    (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
]

ACTIVE_STATES = [
    CoordinationState.CREATED,
    CoordinationState.PLANNING,
    CoordinationState.ARBITRATING,
    CoordinationState.VALIDATING,
    CoordinationState.EXECUTING,
    CoordinationState.VERIFYING,
]

TERMINAL_STATES = [
    CoordinationState.COMPLETED,
    CoordinationState.FAILED,
    CoordinationState.CANCELLED,
    CoordinationState.TIMED_OUT,
]

ALL_STATES = ACTIVE_STATES + TERMINAL_STATES


@pytest.mark.parametrize(
    ("state", "expected"),
    ACTIVE_TRANSITIONS,
)
def test_allowed_next_returns_expected_successor(state, expected):
    assert Workflow.allowed_next(state) == expected


@pytest.mark.parametrize("state", ALL_STATES)
def test_workflow_rejects_self_transition(state):
    assert Workflow.can_transition(state, state) is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (terminal, active)
        for terminal in TERMINAL_STATES
        for active in ACTIVE_STATES
    ],
)
def test_terminal_state_cannot_transition_to_active_state(current, target):
    assert Workflow.can_transition(current, target) is False


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.PLANNING, CoordinationState.CREATED),
        (CoordinationState.ARBITRATING, CoordinationState.CREATED),
        (CoordinationState.ARBITRATING, CoordinationState.PLANNING),
        (CoordinationState.VALIDATING, CoordinationState.CREATED),
        (CoordinationState.VALIDATING, CoordinationState.ARBITRATING),
        (CoordinationState.EXECUTING, CoordinationState.PLANNING),
        (CoordinationState.EXECUTING, CoordinationState.VALIDATING),
        (CoordinationState.VERIFYING, CoordinationState.ARBITRATING),
        (CoordinationState.VERIFYING, CoordinationState.EXECUTING),
    ],
)
def test_workflow_rejects_backward_transition(current, target):
    assert Workflow.can_transition(current, target) is False


@pytest.mark.parametrize(
    ("state", "expected"),
    ACTIVE_TRANSITIONS,
)
def test_next_state_matches_allowed_next(state, expected):
    assert Workflow.next_state(state) == Workflow.allowed_next(state)
    assert Workflow.next_state(state) == expected