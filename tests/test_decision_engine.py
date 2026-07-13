from datetime import UTC, datetime, timedelta

from heos.candidate import Candidate
from heos.decision import Action, Decision, DecisionReason
from heos.decision_engine import DecisionEngine


def make_candidate(
    *,
    action: Action,
    confidence: float,
    priority: int,
    brain_id: str,
) -> Candidate:
    return Candidate(
        decision=Decision(
            action=action,
            confidence=confidence,
            reasons=(DecisionReason("test", "Test reason."),),
            valid_for=timedelta(minutes=1),
        ),
        brain_id=brain_id,
        priority=priority,
    )


def test_engine_selects_highest_scoring_candidate() -> None:
    charge = make_candidate(
        action=Action.CHARGE,
        confidence=0.90,
        priority=80,
        brain_id="ev",
    )
    wait = make_candidate(
        action=Action.WAIT,
        confidence=0.99,
        priority=40,
        brain_id="energy",
    )

    result = DecisionEngine().select((wait, charge))

    assert result.selected is charge
    assert result.decision is charge.decision


def test_engine_rejects_low_confidence_candidate() -> None:
    candidate = make_candidate(
        action=Action.CHARGE,
        confidence=0.40,
        priority=100,
        brain_id="ev",
    )

    result = DecisionEngine(minimum_confidence=0.60).select((candidate,))

    assert result.selected is None
    assert result.rejected == (candidate,)


def test_engine_rejects_expired_candidate() -> None:
    expired = Candidate(
        decision=Decision(
            action=Action.CHARGE,
            confidence=0.99,
            reasons=(DecisionReason("expired", "Expired decision."),),
            valid_for=timedelta(seconds=1),
            created_at=datetime(2020, 1, 1, tzinfo=UTC),
        ),
        brain_id="ev",
        priority=100,
    )

    result = DecisionEngine().select((expired,))

    assert result.selected is None
    assert result.rejected == (expired,)
