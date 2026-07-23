from heos.result_verification import (
    ContextSimilarityEngine,
)


def test_similarity_detects_close_context():

    engine = ContextSimilarityEngine()

    result = engine.compare(
        {
            "pv": 5000,
            "battery": 80,
        },
        {
            "pv": 5000,
            "battery": 90,
        },
    )

    assert result.score == 0.5