from heos.result_verification import (
    DecisionSimulationEngine,
)


def test_simulation_creates_scenarios():

    engine = DecisionSimulationEngine()

    result = engine.simulate(
        [
            ("charge_now", 0.9),
            ("wait", 0.7),
        ]
    )

    assert len(result) == 2
    assert result[0].scenario == "charge_now"
    assert result[0].expected_value == 0.9