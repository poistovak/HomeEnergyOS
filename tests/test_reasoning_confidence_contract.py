from heos.result_verification import (
    ReasoningConfidenceEngine,
)


def test_reasoning_confidence_accepts_value():

    engine = ReasoningConfidenceEngine()

    result = engine.evaluate(
        0.92,
    )

    assert result.confidence == 0.92