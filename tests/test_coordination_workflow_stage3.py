import pytest

from heos.coordination import CoordinationContext, CoordinationState
from heos.coordination.coordinator import CoordinationCoordinator
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    ("current_state", "expected_state"),
    [
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ],
)
def test_all_valid_workflow_transitions(current_state, expected_state):
    assert Workflow.next_state(current_state) == expected_state


@pytest.mark.parametrize(
    "terminal_state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_states_have_no_next_transition(terminal_state):
    with pytest.raises(KeyError):
        Workflow.next_state(terminal_state)


@pytest.mark.parametrize(
    ("current_state", "expected_state"),
    [
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ],
)
def test_coordinator_advances_from_each_active_state(
    current_state,
    expected_state,
):
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="stage3")
    ctx.state = current_state.value

    result = coordinator.advance(ctx)

    assert result.state == expected_state.value


def test_start_returns_same_context_instance():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="same-start")

    result = coordinator.start(ctx)

    assert result is ctx


def test_advance_returns_same_context_instance():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="same-advance")

    coordinator.start(ctx)
    result = coordinator.advance(ctx)

    assert result is ctx


def test_start_is_idempotent():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="idempotent")

    coordinator.start(ctx)
    coordinator.start(ctx)

    assert ctx.state == CoordinationState.PLANNING.value


def test_start_overwrites_existing_state():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="restart")
    ctx.state = CoordinationState.COMPLETED.value

    coordinator.start(ctx)

    assert ctx.state == CoordinationState.PLANNING.value


def test_advance_rejects_unknown_state():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="invalid")
    ctx.state = "UNKNOWN"

    with pytest.raises(ValueError):
        coordinator.advance(ctx)


def test_workflow_contains_six_transitions():
    assert len(Workflow._TRANSITIONS) == 6


def test_terminal_states_are_not_transition_sources():
    terminal_states = {
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    }

    assert terminal_states.isdisjoint(Workflow._TRANSITIONS)


def test_workflow_transition_targets_are_unique():
    targets = list(Workflow._TRANSITIONS.values())

    assert len(targets) == len(set(targets))


def test_full_coordination_cycle_reaches_completed():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="full-cycle")

    coordinator.start(ctx)

    while ctx.state != CoordinationState.COMPLETED.value:
        coordinator.advance(ctx)

    assert ctx.state == CoordinationState.COMPLETED.value


def test_advance_from_completed_state_fails():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="finished")
    ctx.state = CoordinationState.COMPLETED.value

    with pytest.raises(KeyError):
        coordinator.advance(ctx)


def test_cycle_id_is_preserved_during_coordination():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="PALO-750")

    coordinator.start(ctx)
    coordinator.advance(ctx)

    assert ctx.cycle_id == "PALO-750"
