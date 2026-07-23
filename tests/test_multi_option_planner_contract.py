from heos.result_verification import (
    MultiOptionPlanner,
)


def test_planner_ranks_options():

    engine = MultiOptionPlanner()

    result = engine.plan(
        [
            ("charge_now", 0.8),
            ("wait", 0.6),
            ("export", 0.4),
        ]
    )

    assert result[0].name == "charge_now"
    assert result[0].score == 0.8