from datetime import datetime, timezone

from heos.result_verification import (
    DecisionMemory,
    DecisionMemoryRecord,
    DecisionMemoryQuery,
    DecisionMemoryRanker,
    DecisionMemoryRecommender,
    DecisionQuery,
)


def test_recommends_best_decision():

    memory = DecisionMemory()

    memory.add(
        DecisionMemoryRecord(
            command_id="cmd-084",
            decision="increase_charge",
            outcome="SUCCESS",
            expected_value=5000,
            actual_value=4900,
            success=True,
            created_at=datetime.now(timezone.utc),
        )
    )

    recommender = DecisionMemoryRecommender(
        DecisionMemoryQuery(memory),
        DecisionMemoryRanker(),
    )

    result = recommender.recommend(
        DecisionQuery(
            decision="increase_charge",
            success_only=True,
        )
    )

    assert result is not None
    assert result.decision == "increase_charge"