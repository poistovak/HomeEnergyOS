from heos.result_verification import (
    LearningFeedbackLoopEngine,
)


def test_feedback_accepts_improvement():

    engine = LearningFeedbackLoopEngine()

    result = engine.evaluate(
        0.15,
    )

    assert result.improvement == 0.15
    assert result.accepted is True