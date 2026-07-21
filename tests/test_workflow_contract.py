import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


TRANSITIONS = (
    (CoordinationState.CREATED, CoordinationState.PLANNING),
    (CoordinationState.PLANNING, CoordinationState.ARBITRATING),
    (CoordinationState.ARBITRATING, CoordinationState.VALIDATING),
    (CoordinationState.VALIDATING, CoordinationState.EXECUTING),
    (CoordinationState.EXECUTING, CoordinationState.VERIFYING),
    (CoordinationState.VERIFYING, CoordinationState.COMPLETED),
)


@pytest.mark.parametrize(("src", "dst"), TRANSITIONS)
def test_transition_contract(src, dst):
    assert Workflow.allowed_next(src) == dst
    assert Workflow.next_state(src) == dst
    assert Workflow.can_transition(src, dst)


@pytest.mark.parametrize(("src", "dst"), TRANSITIONS)
def test_transition_is_deterministic(src, dst):
    assert Workflow.next_state(src) == Workflow.next_state(src)
    assert Workflow.allowed_next(src) == Workflow.allowed_next(src)