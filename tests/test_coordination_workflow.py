import pytest

from heos.coordination import CoordinationContext, CoordinationState
from heos.coordination.coordinator import CoordinationCoordinator
from heos.coordination.workflow import Workflow


def test_workflow_first_step():
    assert (
        Workflow.next_state(CoordinationState.CREATED)
        == CoordinationState.PLANNING
    )


def test_workflow_last_step():
    assert (
        Workflow.next_state(CoordinationState.VERIFYING)
        == CoordinationState.COMPLETED
    )


def test_coordinator_start():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="001")

    coordinator.start(ctx)

    assert ctx.state == "PLANNING"


def test_coordinator_advance():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="001")

    coordinator.start(ctx)
    coordinator.advance(ctx)

    assert ctx.state == "ARBITRATING"


def test_workflow_complete_path():
    state = CoordinationState.CREATED

    expected_states = [
        CoordinationState.PLANNING,
        CoordinationState.ARBITRATING,
        CoordinationState.VALIDATING,
        CoordinationState.EXECUTING,
        CoordinationState.VERIFYING,
        CoordinationState.COMPLETED,
    ]

    for expected in expected_states:
        state = Workflow.next_state(state)
        assert state == expected


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
def test_all_state_transitions(current, expected):
    assert Workflow.next_state(current) == expected


@pytest.mark.parametrize(
    "state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_terminal_state_has_no_next_state(state):
    with pytest.raises(KeyError):
        Workflow.next_state(state)


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
    "state",
    [
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ],
)
def test_allowed_next_returns_none_for_terminal_state(state):
    assert Workflow.allowed_next(state) is None


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
def test_can_transition_accepts_valid_direct_transition(current, target):
    assert Workflow.can_transition(current, target) is True


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.EXECUTING),
        (CoordinationState.PLANNING, CoordinationState.COMPLETED),
        (CoordinationState.ARBITRATING, CoordinationState.EXECUTING),
        (CoordinationState.VALIDATING, CoordinationState.VERIFYING),
        (CoordinationState.EXECUTING, CoordinationState.COMPLETED),
        (CoordinationState.COMPLETED, CoordinationState.CREATED),
    ],
)
def test_can_transition_rejects_invalid_transition(current, target):
    assert Workflow.can_transition(current, target) is False


def test_era3_start_returns_same_context():
    coordinator = CoordinationCoordinator()
    context = CoordinationContext(cycle_id="era3-001")

    result = coordinator.start(context)

    assert result is context


def test_era3_advance_returns_same_context():
    coordinator = CoordinationCoordinator()
    context = CoordinationContext(
        cycle_id="era3-002",
        state="PLANNING",
    )

    result = coordinator.advance(context)

    assert result is context


@pytest.mark.parametrize(
    ("current_state", "expected_state"),
    [
        ("PLANNING", "ARBITRATING"),
        ("ARBITRATING", "VALIDATING"),
        ("VALIDATING", "EXECUTING"),
        ("EXECUTING", "VERIFYING"),
        ("VERIFYING", "COMPLETED"),
    ],
)
def test_era3_coordinator_advances_energy_cycle(
    current_state,
    expected_state,
):
    coordinator = CoordinationCoordinator()
    context = CoordinationContext(
        cycle_id=f"energy-{current_state.lower()}",
        state=current_state,
    )

    coordinator.advance(context)

    assert context.state == expected_state


def test_era3_context_has_safe_defaults():
    context = CoordinationContext(cycle_id="era3-defaults")

    assert context.source == "unknown"
    assert context.request == {}
    assert context.metadata == {}
    assert context.state == "CREATED"


def test_era3_request_data_is_isolated_between_cycles():
    first = CoordinationContext(cycle_id="era3-request-1")
    second = CoordinationContext(cycle_id="era3-request-2")

    first.request["house_power_w"] = 4200

    assert second.request == {}


def test_era3_metadata_is_isolated_between_cycles():
    first = CoordinationContext(cycle_id="era3-meta-1")
    second = CoordinationContext(cycle_id="era3-meta-2")

    first.metadata["pv_surplus_w"] = 3100

    assert second.metadata == {}


def test_era3_context_timestamp_is_timezone_aware():
    context = CoordinationContext(cycle_id="era3-time")

    assert context.created_at.tzinfo is not None
    assert context.created_at.utcoffset() is not None


def test_era3_start_always_enters_planning():
    coordinator = CoordinationCoordinator()
    context = CoordinationContext(
        cycle_id="era3-restart",
        state="FAILED",
    )

    coordinator.start(context)

    assert context.state == "PLANNING"


def test_era3_completed_cycle_cannot_advance():
    coordinator = CoordinationCoordinator()
    context = CoordinationContext(
        cycle_id="era3-terminal",
        state="COMPLETED",
    )

    with pytest.raises(KeyError):
        coordinator.advance(context)
