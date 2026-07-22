from heos.result_verification import (
    DecisionTrustEngine,
)


def test_trust_is_average_of_history():

    engine = DecisionTrustEngine()

    result = engine.evaluate(
        "charge",
        [
            0.7,
            0.8,
            0.9,
        ],
    )

    assert result.recommendation == "charge"
    assert result.samples == 3
    assert result.trust == 0.8