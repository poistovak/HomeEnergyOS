import pytest

from heos.coordination import CoordinationState
from heos.coordination.workflow import Workflow


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (CoordinationState.CREATED, CoordinationState.ARBITRATING),
        (CoordinationState.CREATED, CoordinationState.VERIFYING),
        (CoordinationState.CREATED, CoordinationState.FAILED),
        (CoordinationState.CREATED, CoordinationState.CANCELLED),
        (CoordinationState.PLANNING, CoordinationState.VALIDATING),
        (CoordinationState.PLANNING, CoordinationState.FAILED),
        (CoordinationState.PLANNING, CoordinationState.TIMED_OUT),
        (CoordinationState.ARBITRATING, CoordinationState.CREATED),
        (CoordinationState.ARBITRATING, CoordinationState.VERIFYING),
        (CoordinationState.ARBITRATING, CoordinationState.CANCELLED),
        (CoordinationState.VALIDATING, CoordinationState.PLANNING),
        (CoordinationState.VALIDATING, CoordinationState.COMPLETED),
        (CoordinationState.VALIDATING, CoordinationState.TIMED_OUT),
        (CoordinationState.EXECUTING, CoordinationState.ARBITRATING),
        (CoordinationState.EXECUTING, CoordinationState.FAILED),
        (CoordinationState.EXECUTING, CoordinationState.CANCELLED),
        (CoordinationState.VERIFYING, CoordinationState.PLANNING),
        (CoordinationState.VERIFYING, CoordinationState.FAILED),
        (CoordinationState.VERIFYING, CoordinationState.CANCELLED),
        (CoordinationState.VERIFYING, CoordinationState.TIMED_OUT),
    ],
)
def test_final_push_rejects_illegal_transitions(current, target):
    assert Workflow.can_transition(current, target) is False