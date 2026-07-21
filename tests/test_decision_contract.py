from datetime import UTC, datetime, timedelta

import pytest

from heos.domain.decision import Action, Decision, DecisionReason


def reason():
    return DecisionReason(code="R1", message="Test reason")


def test_decision_requires_reason():
    with pytest.raises(ValueError, match="at least one reason"):
        Decision(
            action=Action.WAIT,
            confidence=0.5,
            reasons=(),
        )


@pytest.mark.parametrize("confidence", (-0.1, 1.1))
def test_invalid_confidence(confidence):
    with pytest.raises(ValueError, match="confidence"):
        Decision(
            action=Action.WAIT,
            confidence=confidence,
            reasons=(reason(),),
        )


def test_expires_at_is_created_plus_valid_for():
    created = datetime(2026, 1, 1, tzinfo=UTC)

    decision = Decision(
        action=Action.WAIT,
        confidence=0.5,
        reasons=(reason(),),
        created_at=created,
        valid_for=timedelta(seconds=30),
    )

    assert decision.expires_at == created + timedelta(seconds=30)


def test_explain_contains_reason_message():
    decision = Decision(
        action=Action.CHARGE,
        confidence=0.9,
        reasons=(
            DecisionReason(code="A", message="Battery low"),
            DecisionReason(code="B", message="PV surplus"),
        ),
    )

    assert decision.explain() == "Battery low PV surplus"


def test_not_expired_before_expiration():
    created = datetime(2026, 1, 1, tzinfo=UTC)

    decision = Decision(
        action=Action.WAIT,
        confidence=0.5,
        reasons=(reason(),),
        created_at=created,
        valid_for=timedelta(minutes=5),
    )

    assert not decision.is_expired(created + timedelta(minutes=4))


def test_expired_after_expiration():
    created = datetime(2026, 1, 1, tzinfo=UTC)

    decision = Decision(
        action=Action.WAIT,
        confidence=0.5,
        reasons=(reason(),),
        created_at=created,
        valid_for=timedelta(minutes=5),
    )

    assert decision.is_expired(created + timedelta(minutes=6))