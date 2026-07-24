import pytest

from heos.coordination.state import CoordinationState

EXPECTED_STATES = (
    "CREATED",
    "PLANNING",
    "ARBITRATING",
    "VALIDATING",
    "EXECUTING",
    "VERIFYING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMED_OUT",
)


@pytest.mark.parametrize("name", EXPECTED_STATES)
def test_state_exists(name):
    assert CoordinationState[name].name == name


@pytest.mark.parametrize("value", EXPECTED_STATES)
def test_state_value_matches_name(value):
    state = CoordinationState(value)

    assert state.value == value
    assert state.name == value


def test_state_count():
    assert len(CoordinationState) == 10


def test_state_values_are_unique():
    values = [state.value for state in CoordinationState]

    assert len(values) == len(set(values))