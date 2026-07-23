from heos.result_verification import (
    ExperienceRankingEngine,
)


def test_experience_ranking_orders_best_first():

    engine = ExperienceRankingEngine()

    result = engine.rank(
        [
            ("case_a", 0.70),
            ("case_b", 0.95),
            ("case_c", 0.80),
        ]
    )

    assert result[0].experience == "case_b"
    assert result[0].score == 0.95
    assert result[1].experience == "case_c"