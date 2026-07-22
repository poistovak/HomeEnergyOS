from heos.result_verification import (
    ConsolidatedDecisionMemory,
    DecisionConfidenceEngine,
)


def test_confidence_orders_best_memory_first():

    engine = DecisionConfidenceEngine()

    result = engine.evaluate(
        [
            ConsolidatedDecisionMemory(
                recommendation="slow_charge",
                total=10,
                successful=5,
                confidence=0.5,
            ),
            ConsolidatedDecisionMemory(
                recommendation="fast_charge",
                total=20,
                successful=18,
                confidence=0.9,
            ),
        ]
    )

    assert result[0].recommendation == "fast_charge"
    assert result[0].confidence == 0.9