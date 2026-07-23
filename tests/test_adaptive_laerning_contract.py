from heos.result_verification import (
    AdaptiveLearningEngine,
)


def test_learning_creates_signal():

    engine = AdaptiveLearningEngine()

    result = engine.learn(
        "better_ev_charging_time",
        0.85,
    )

    assert result.experience == "better_ev_charging_time"
    assert result.improvement == 0.85