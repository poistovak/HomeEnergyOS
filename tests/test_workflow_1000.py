import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (CoordinationState.CREATED, False),
        (CoordinationState.PLANNING, False),
        (CoordinationState.ARBITRATING, False),
        (CoordinationState.VALIDATING, False),
        (CoordinationState.EXECUTING, False),
        (CoordinationState.VERIFYING, False),
        (CoordinationState.COMPLETED, True),
        (CoordinationState.FAILED, True),
        (CoordinationState.CANCELLED, True),
        (CoordinationState.TIMED_OUT, True),
    ],
)
def test_terminal_flags(state, expected):
    assert Workflow.is_terminal(state) is expected


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
def test_allowed_next_exists(state):
    assert Workflow.allowed_next(state) is not None