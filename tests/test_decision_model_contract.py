from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest

from heos.domain.decision import Action, Decision, DecisionReason


def make_reason():
    return DecisionReason(
        code="PV001",
        message="PV surplus",
    )


def make_decision():
    return Decision(
        action=Action.CHARGE,
        confidence=0.8,
        reasons=(make_reason(),),
    )


def test_decision_defaults():
    d = make_decision()

    assert d.parameters == {}
    assert d.valid_for == timedelta(seconds=60)
    assert d.created_at is not None
    assert d.decision_id is not None


def test_decision_is_frozen():
    d = make_decision()

    with pytest.raises(FrozenInstanceError):
        d.confidence = 0.5


def test_reason_is_frozen():
    r = make_reason()

    with pytest.raises(FrozenInstanceError):
        r.message = "Changed"


def test_parameters_are_independent():
    a = make_decision()
    b = make_decision()

    a.parameters["power"] = 5000

    assert "power" not in b.parameters


@pytest.mark.parametrize("action", list(Action))
def test_every_action_creates_decision(action):
    d = Decision(
        action=action,
        confidence=0.5,
        reasons=(make_reason(),),
    )

    assert d.action is action


@pytest.mark.parametrize(
    "seconds",
    [1, 10, 60, 300, 3600],
)
def test_valid_for_positive(seconds):
    d = Decision(
        action=Action.WAIT,
        confidence=0.5,
        reasons=(make_reason(),),
        valid_for=timedelta(seconds=seconds),
    )

    assert d.valid_for.total_seconds() == seconds