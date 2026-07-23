from heos.result_verification import (
    DecisionExplanationEngine,
)


def test_explanation_contains_reasons():

    engine = DecisionExplanationEngine()

    result = engine.explain(
        "charge",
        [
            "high PV surplus",
            "battery available",
        ],
    )

    assert result.decision == "charge"
    assert len(result.reasons) == 2