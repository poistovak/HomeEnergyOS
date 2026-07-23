from heos.result_verification import (
    DecisionIntelligenceOrchestrator,
)


def test_orchestrator_creates_final_decision():

    engine = DecisionIntelligenceOrchestrator()

    result = engine.decide(
        "charge",
        0.95,
    )

    assert result.recommendation == "charge"
    assert result.confidence == 0.95