from datetime import UTC, datetime

from heos.result_verification import (
    DecisionFeedback,
    DecisionMemoryConsolidator,
)


def test_consolidates_feedback():

    consolidator = DecisionMemoryConsolidator()

    feedback = [
        DecisionFeedback(
            command_id="1",
            recommendation="charge",
            outcome="SUCCESS",
            success=True,
            created_at=datetime.now(UTC),
        ),
        DecisionFeedback(
            command_id="2",
            recommendation="charge",
            outcome="SUCCESS",
            success=True,
            created_at=datetime.now(UTC),
        ),
        DecisionFeedback(
            command_id="3",
            recommendation="charge",
            outcome="FAILED",
            success=False,
            created_at=datetime.now(UTC),
        ),
    ]

    result = consolidator.consolidate(
        feedback
    )

    assert len(result) == 1
    assert result[0].recommendation == "charge"
    assert result[0].total == 3
    assert result[0].successful == 2
    assert result[0].confidence == 2 / 3