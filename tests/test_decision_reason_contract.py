from dataclasses import FrozenInstanceError

import pytest

from heos.domain.decision import DecisionReason


def test_reason_fields():
    reason = DecisionReason(
        code="PV001",
        message="PV surplus available",
        weight=0.75,
    )

    assert reason.code == "PV001"
    assert reason.message == "PV surplus available"
    assert reason.weight == 0.75


def test_default_weight():
    reason = DecisionReason(
        code="A",
        message="Default",
    )

    assert reason.weight == 1.0


@pytest.mark.parametrize(
    ("weight",),
    (
        (0.0,),
        (0.5,),
        (1.0,),
        (2.0,),
    ),
)
def test_custom_weights(weight):
    reason = DecisionReason(
        code="X",
        message="Reason",
        weight=weight,
    )

    assert reason.weight == weight


def test_reason_is_frozen():
    reason = DecisionReason(
        code="A",
        message="Immutable",
    )

    with pytest.raises(FrozenInstanceError):
        reason.code = "B"


def test_equal_objects_compare_equal():
    a = DecisionReason("A", "Message", 1.0)
    b = DecisionReason("A", "Message", 1.0)

    assert a == b


def test_different_objects_compare_not_equal():
    a = DecisionReason("A", "Message", 1.0)
    b = DecisionReason("B", "Other", 1.0)

    assert a != b