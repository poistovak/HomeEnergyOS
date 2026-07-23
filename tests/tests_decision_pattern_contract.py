from heos.result_verification import (
    DecisionPatternEngine,
)


def test_pattern_detects_success_rate():

    engine = DecisionPatternEngine()

    result = engine.analyze(
        "charge",
        [
            True,
            True,
            True,
            False,
        ],
    )

    assert result.recommendation == "charge"
    assert result.occurrences == 4
    assert result.score == 0.75