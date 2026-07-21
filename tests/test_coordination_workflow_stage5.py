import pytest

from heos.coordination.state import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ],
)
def test_valid_direct_transitions_are_accepted(current, target):
    assert Workflow.can_transition(current, target) is True


@pytest.mark.parametrize(
    "state",
    list(CoordinationState),
)
def test_state_cannot_transition_to_itself(state):
    assert Workflow.can_transition(state, state) is False


@pytest.mark.parametrize(
    "terminal_state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_state_cannot_restart_directly(terminal_state):
    assert (
        Workflow.can_transition(
            terminal_state,
            CoordinationState.PLANNING,
        )
        is False
    )


def test_active_and_terminal_states_cover_complete_enum():
    active_states = set(Workflow._TRANSITIONS)
    terminal_states = set(Workflow._TERMINAL_STATES)

    assert active_states | terminal_states == set(CoordinationState)


def test_active_and_terminal_states_do_not_overlap():
    active_states = set(Workflow._TRANSITIONS)
    terminal_states = set(Workflow._TERMINAL_STATES)

    assert active_states.isdisjoint(terminal_states)


def test_all_transition_targets_are_known_states():
    assert set(Workflow._TRANSITIONS.values()) <= set(CoordinationState)


def test_workflow_path_has_expected_order():
    state = CoordinationState.CREATED
    path = [state]

    while not Workflow.is_terminal(state):
        state = Workflow.next_state(state)
        path.append(state)

    assert path == [
        CoordinationState.CREATED,
        CoordinationState.PLANNING,
        CoordinationState.ARBITRATING,
        CoordinationState.VALIDATING,
        CoordinationState.EXECUTING,
        CoordinationState.VERIFYING,
        CoordinationState.COMPLETED,
    ]


def test_next_state_and_allowed_next_are_consistent():
    for state in Workflow._TRANSITIONS:
        assert Workflow.next_state(state) == Workflow.allowed_next(state)
