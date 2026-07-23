from heos.result_verification import (
    ExperienceSynthesisEngine,
)


def test_synthesis_combines_experiences():

    engine = ExperienceSynthesisEngine()

    result = engine.synthesize(
        "charge",
        [
            0.9,
            0.8,
            1.0,
        ],
    )

    assert result.recommendation == "charge"
    assert result.confidence == 0.9