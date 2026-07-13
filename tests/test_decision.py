import pytest

from heos.decision import Action, Decision


def test_decision_requires_reason() -> None:
    with pytest.raises(ValueError, match="at least one reason"):
        Decision(Action.WAIT, 0.5, ())
