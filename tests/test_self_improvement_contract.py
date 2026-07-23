from heos.result_verification import (
    SelfImprovementEngine,
)


def test_self_improvement_creates_proposal():

    engine = SelfImprovementEngine()

    result = engine.propose(
        "ev_charging_strategy",
        0.10,
    )

    assert result.area == "ev_charging_strategy"
    assert result.expected_gain == 0.10