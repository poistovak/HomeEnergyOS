from heos.result_verification import (
    ReasoningOrchestrator,
)


def test_reasoning_orchestrator_creates_result():

    engine = ReasoningOrchestrator()

    result = engine.create_result(
        "charge",
        0.95,
    )

    assert result.decision == "charge"
    assert result.confidence == 0.95