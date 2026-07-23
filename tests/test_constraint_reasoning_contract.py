from heos.result_verification import (
    ConstraintReasoningEngine,
)


def test_constraint_allows_safe_action():

    engine = ConstraintReasoningEngine()

    result = engine.evaluate(
        True,
        "power available",
    )

    assert result.allowed is True
    assert result.reason == "power available"