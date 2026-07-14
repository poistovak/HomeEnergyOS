from datetime import timedelta

from heos.arbitration import (
    ArbitrationCandidate,
    DecisionArbitrator,
)
from heos.planning import (
    FutureScenario,
    ScenarioMetrics,
)


def scenario(
    scenario_id: str,
    *,
    score: float,
    confidence: float = 1.0,
) -> FutureScenario:
    return FutureScenario(
        scenario_id=scenario_id,
        title=scenario_id,
        actions=(),
        metrics=ScenarioMetrics(
            confidence=confidence,
        ),
        score=score,
        reasons=("test",),
        horizon=timedelta(minutes=15),
    )


def test_highest_valid_score_wins() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario("wait", score=10),
            ),
            ArbitrationCandidate(
                scenario("charge_ev", score=90),
            ),
            ArbitrationCandidate(
                scenario("export", score=40),
            ),
        )
    )

    assert report.winner_id == "charge_ev"
    assert report.decided is True


def test_invalid_high_score_cannot_win() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario("unsafe", score=100),
                valid=False,
                rejection_reason="Rejected by policy.",
            ),
            ArbitrationCandidate(
                scenario("safe", score=60),
            ),
        )
    )

    assert report.winner_id == "safe"
    assert report.ranking[0].scenario_id == "safe"
    assert any(
        item.scenario_id == "unsafe" and not item.valid
        for item in report.ranking
    )


def test_policy_priority_overrides_scenario_score() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario("battery", score=99),
                policy_priority=0,
            ),
            ArbitrationCandidate(
                scenario("human_request", score=50),
                policy_priority=10,
            ),
        )
    )

    assert report.winner_id == "human_request"


def test_confidence_breaks_equal_score_tie() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario(
                    "low_confidence",
                    score=80,
                    confidence=0.60,
                )
            ),
            ArbitrationCandidate(
                scenario(
                    "high_confidence",
                    score=80,
                    confidence=0.95,
                )
            ),
        )
    )

    assert report.winner_id == "high_confidence"


def test_scenario_id_breaks_complete_tie_deterministically() -> None:
    arbitrator = DecisionArbitrator()
    candidates = (
        ArbitrationCandidate(
            scenario("b_scenario", score=80, confidence=0.9)
        ),
        ArbitrationCandidate(
            scenario("a_scenario", score=80, confidence=0.9)
        ),
    )

    first = arbitrator.arbitrate(candidates)
    second = arbitrator.arbitrate(reversed(candidates))

    assert first.winner_id == "a_scenario"
    assert second.winner_id == "a_scenario"
    assert first.ranking == second.ranking


def test_no_candidates_produces_no_winner() -> None:
    report = DecisionArbitrator().arbitrate(())

    assert report.winner is None
    assert report.decided is False
    assert report.ranking == ()


def test_all_invalid_candidates_produce_no_winner() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario("a", score=90),
                valid=False,
                rejection_reason="Invalid A.",
            ),
            ArbitrationCandidate(
                scenario("b", score=80),
                valid=False,
                rejection_reason="Invalid B.",
            ),
        )
    )

    assert report.winner is None
    assert report.decided is False


def test_report_contains_explainable_trace() -> None:
    report = DecisionArbitrator().arbitrate(
        (
            ArbitrationCandidate(
                scenario("charge_ev", score=90),
                policy_priority=5,
            ),
            ArbitrationCandidate(
                scenario("wait", score=10),
            ),
        )
    )

    assert report.trace[0].stage == "input"
    assert report.trace[-1].stage == "decision"
    assert "charge_ev" in report.trace[-1].message


def test_invalid_candidate_requires_rejection_reason() -> None:
    try:
        ArbitrationCandidate(
            scenario("invalid", score=1),
            valid=False,
        )
    except ValueError as error:
        assert "rejection_reason" in str(error)
    else:
        raise AssertionError("Expected ValueError")
