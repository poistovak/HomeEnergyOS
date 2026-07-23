from heos.result_verification import (
    CausalRelationshipEngine,
)


def test_causal_relationship_creation():

    engine = CausalRelationshipEngine()

    result = engine.create(
        "low_solar_generation",
        "battery_low",
        0.8,
    )

    assert result.cause == "low_solar_generation"
    assert result.effect == "battery_low"
    assert result.strength == 0.8