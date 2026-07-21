import pytest

from heos.coordination.context import CoordinationContext
from heos.coordination.coordinator import CoordinationCoordinator
from heos.coordination.state import CoordinationState


def test_start_moves_context_to_planning():
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(cycle_id="1")

    result = coordinator.start(ctx)

    assert result is ctx
    assert ctx.state == CoordinationState.PLANNING.value


@pytest.mark.parametrize(
    ("initial", "expected"),
    (
        (CoordinationState.CREATED, CoordinationState.PLANNING),
        (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
        (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
        (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
        (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
        (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
    ),
)
def test_advance_moves_to_next_state(initial, expected):
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(
        cycle_id="1",
        state=initial.value,
    )

    result = coordinator.advance(ctx)

    assert result is ctx
    assert ctx.state == expected.value


@pytest.mark.parametrize(
    "terminal",
    (
        CoordinationState.COMPLETED,
        CoordinationState.FAILED,
        CoordinationState.CANCELLED,
        CoordinationState.TIMED_OUT,
    ),
)
def test_advance_terminal_state_raises_key_error(terminal):
    coordinator = CoordinationCoordinator()
    ctx = CoordinationContext(
        cycle_id="1",
        state=terminal.value,
    )

    with pytest.raises(KeyError):
        coordinator.advance(ctx)