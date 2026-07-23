from heos.result_verification import (
    CounterfactualReasoningEngine,
)


def test_counterfactual_compares_options():

    engine = CounterfactualReasoningEngine()

    result = engine.compare(
        "charge",
        "wait",
        0.9,
        0.6,
    )

    assert result.actual == "charge"
    assert result.alternative == "wait"
    assert result.difference == 0.3