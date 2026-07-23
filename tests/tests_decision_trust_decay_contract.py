from heos.result_verification import (
    DecisionTrustDecayEngine,
)


def test_trust_decay_reduces_old_confidence():

    engine = DecisionTrustDecayEngine()

    result = engine.apply(
        "charge",
        0.9,
        0.95,
    )

    assert result.recommendation == "charge"
    assert result.trust == 0.855
    assert result.decay_factor == 0.95