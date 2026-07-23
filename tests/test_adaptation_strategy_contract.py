from heos.result_verification import (
    AdaptationStrategyEngine,
)


def test_adaptation_accepts_good_strategy():

    engine = AdaptationStrategyEngine()

    result = engine.evaluate(
        "optimize_ev_charging",
        0.9,
    )

    assert result.strategy == "optimize_ev_charging"
    assert result.accepted is True