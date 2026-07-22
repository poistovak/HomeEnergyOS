from datetime import datetime, timezone

from heos.result_verification import (
    DecisionFeedback,
    DecisionFeedbackMemory,
)


def test_feedback_memory_stores_result():

    memory = DecisionFeedbackMemory()

    feedback = DecisionFeedback(
        command_id="cmd-085",
        recommendation="increase_power",
        outcome="SUCCESS",
        success=True,
        created_at=datetime.now(timezone.utc),
    )

    memory.add(feedback)

    assert len(memory.all()) == 1
    assert memory.all()[0].success is True


def test_successful_feedback_filter():

    memory = DecisionFeedbackMemory()

    memory.add(
        DecisionFeedback(
            command_id="cmd-ok",
            recommendation="charge",
            outcome="SUCCESS",
            success=True,
            created_at=datetime.now(timezone.utc),
        )
    )

    memory.add(
        DecisionFeedback(
            command_id="cmd-fail",
            recommendation="charge",
            outcome="FAILED",
            success=False,
            created_at=datetime.now(timezone.utc),
        )
    )

    assert len(memory.successful()) == 1