import pytest

from heos.domain.decision import Action

EXPECTED_ACTIONS = (
    "CHARGE",
    "PREPARE",
    "WAIT",
    "STOP",
    "HEAT_WATER",
    "PRECOOL",
    "EXPORT",
)


@pytest.mark.parametrize("name", EXPECTED_ACTIONS)
def test_action_exists(name):
    assert Action[name].name == name


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("CHARGE", "charge"),
        ("PREPARE", "prepare"),
        ("WAIT", "wait"),
        ("STOP", "stop"),
        ("HEAT_WATER", "heat_water"),
        ("PRECOOL", "precool"),
        ("EXPORT", "export"),
    ),
)
def test_action_values(name, value):
    assert Action[name].value == value


def test_action_count():
    assert len(Action) == 7


def test_action_values_are_unique():
    values = [action.value for action in Action]
    assert len(values) == len(set(values))


def test_action_lookup_by_value():
    for action in Action:
        assert Action(action.value) is action


def test_action_names_are_unique():
    names = [action.name for action in Action]
    assert len(names) == len(set(names))