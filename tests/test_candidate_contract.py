from dataclasses import FrozenInstanceError

import pytest

from heos.candidate import Candidate
from heos.decision import Action, Decision, DecisionReason


def make_decision(confidence: float = 0.5) -> Decision:
    return Decision(
        action=Action.WAIT,
        confidence=confidence,
        reasons=(DecisionReason(code="test", message="Test reason"),),
    )


@pytest.mark.parametrize("priority", (0, 1, 50, 99, 100))
def test_valid_priority(priority):
    candidate = Candidate(
        decision=make_decision(),
        brain_id="brain-1",
        priority=priority,
    )

    assert candidate.priority == priority


@pytest.mark.parametrize("priority", (-100, -1, 101, 500))
def test_invalid_priority_raises(priority):
    with pytest.raises(ValueError, match="priority must be between 0 and 100"):
        Candidate(
            decision=make_decision(),
            brain_id="brain-1",
            priority=priority,
        )


@pytest.mark.parametrize("utility", (-1.0, -0.5, 0.0, 0.5, 1.0))
def test_valid_utility(utility):
    candidate = Candidate(
        decision=make_decision(),
        brain_id="brain-1",
        priority=10,
        utility=utility,
    )

    assert candidate.utility == utility


@pytest.mark.parametrize("utility", (-10.0, -1.01, 1.01, 10.0))
def test_invalid_utility_raises(utility):
    with pytest.raises(ValueError, match="utility must be between -1.0 and 1.0"):
        Candidate(
            decision=make_decision(),
            brain_id="brain-1",
            priority=10,
            utility=utility,
        )


@pytest.mark.parametrize(
    ("priority", "confidence", "utility", "expected"),
    (
        (0, 0.0, 0.0, 0.0),
        (10, 0.5, 0.0, 60.0),
        (50, 1.0, 0.0, 150.0),
        (20, 0.5, 1.0, 90.0),
        (20, 0.5, -1.0, 50.0),
    ),
)
def test_score_formula(priority, confidence, utility, expected):
    candidate = Candidate(
        decision=make_decision(confidence),
        brain_id="brain-1",
        priority=priority,
        utility=utility,
    )

    assert candidate.score == expected


def test_default_utility_is_zero():
    candidate = Candidate(
        decision=make_decision(),
        brain_id="brain-1",
        priority=10,
    )

    assert candidate.utility == 0.0


def test_candidate_keeps_original_decision():
    decision = make_decision()

    candidate = Candidate(
        decision=decision,
        brain_id="brain-1",
        priority=10,
    )

    assert candidate.decision is decision


def test_candidate_is_frozen():
    candidate = Candidate(
        decision=make_decision(),
        brain_id="brain-1",
        priority=10,
    )

    with pytest.raises(FrozenInstanceError):
        candidate.priority = 20