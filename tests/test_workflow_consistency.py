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

TERMINAL = (
    CoordinationState.COMPLETED,
    CoordinationState.FAILED,
    CoordinationState.CANCELLED,
    CoordinationState.TIMED_OUT,
)


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ),
)
def test_allowed_next_matches_workflow(state, expected):
    assert Workflow.allowed_next(state) == expected


@pytest.mark.parametrize("state", ACTIVE)
def test_next_state_is_repeatable(state):
    assert Workflow.next_state(state) == Workflow.next_state(state)


@pytest.mark.parametrize("state", ACTIVE)
def test_transition_only_to_allowed_state(state):
    allowed = Workflow.allowed_next(state)

    for target in CoordinationState:
        if target == allowed:
            assert Workflow.can_transition(state, target)
        elif target != state:
            assert Workflow.can_transition(state, target) is False


@pytest.mark.parametrize("state", TERMINAL)
def test_terminal_has_no_allowed_transition(state):
    assert Workflow.allowed_next(state) is None