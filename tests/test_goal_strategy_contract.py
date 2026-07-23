from heos.result_verification import (
    GoalStrategyEngine,
)


def test_goal_strategy_creates_goal():

    engine = GoalStrategyEngine()

    result = engine.evaluate(
        "maximize_self_consumption",
        0.9,
    )

    assert result.goal == "maximize_self_consumption"
    assert result.priority == 0.9