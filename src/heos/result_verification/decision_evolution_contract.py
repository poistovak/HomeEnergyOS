from heos.result_verification import (
    DecisionEvolutionEngine,
)


def test_evolution_detects_improvement():

    engine = DecisionEvolutionEngine()

    result = engine.evaluate(
        "charge",
        [
            0.6,
            0.75,
            0.9,
        ],
    )

    assert result.recommendation == "charge"
    assert result.trend == "improving"
    assert result.score == 0.3