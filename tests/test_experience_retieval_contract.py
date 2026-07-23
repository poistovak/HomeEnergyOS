from heos.result_verification import (
    ExperienceRetrievalEngine,
)


def test_retrieval_returns_best_experience():

    engine = ExperienceRetrievalEngine()

    result = engine.retrieve(
        [
            ("charge_case_1", 0.75),
            ("charge_case_2", 0.95),
            ("charge_case_3", 0.60),
        ]
    )

    assert result.experience == "charge_case_2"
    assert result.score == 0.95