from datetime import UTC, datetime

from heos.result_verification.decision_memory import (
    DecisionMemory,
    DecisionMemoryRecord,
)
from heos.result_verification.decision_orchestrator import (
    DecisionIntelligenceOrchestrator,
)
from heos.result_verification.decision_query import (
    DecisionMemoryQuery,
    DecisionQuery,
)
from heos.result_verification.decision_rank import (
    DecisionMemoryRanker,
)
from heos.result_verification.decision_recommendation import (
    DecisionMemoryRecommender,
)


def make_record(
    *,
    command_id: str,
    decision: str,
    success: bool,
) -> DecisionMemoryRecord:
    return DecisionMemoryRecord(
        command_id=command_id,
        decision=decision,
        outcome="SUCCESS" if success else "FAILED",
        expected_value=5000.0,
        actual_value=4900.0 if success else 3500.0,
        success=success,
        created_at=datetime.now(UTC),
    )


def test_recalled_experience_produces_future_decision():
    memory = DecisionMemory()

    memory.add(
        make_record(
            command_id="cmd-001",
            decision="charge_battery",
            success=True,
        )
    )
    memory.add(
        make_record(
            command_id="cmd-002",
            decision="reduce_charging",
            success=False,
        )
    )

    recommender = DecisionMemoryRecommender(
        query=DecisionMemoryQuery(memory),
        ranker=DecisionMemoryRanker(),
    )

    recommendation = recommender.recommend(
        DecisionQuery()
    )

    assert recommendation is not None
    assert recommendation.decision == "charge_battery"

    orchestrator = DecisionIntelligenceOrchestrator()

    outcome = orchestrator.decide(
        recommendation=recommendation.decision,
        confidence=recommendation.confidence,
    )

    assert outcome.recommendation == "charge_battery"
    assert outcome.confidence == 0.5


def test_recommendation_confidence_reflects_memory_success_rate():
    memory = DecisionMemory()

    memory.add(
        make_record(
            command_id="cmd-001",
            decision="charge_battery",
            success=True,
        )
    )
    memory.add(
        make_record(
            command_id="cmd-002",
            decision="charge_battery",
            success=True,
        )
    )
    memory.add(
        make_record(
            command_id="cmd-003",
            decision="charge_battery",
            success=False,
        )
    )

    recommender = DecisionMemoryRecommender(
        query=DecisionMemoryQuery(memory),
        ranker=DecisionMemoryRanker(),
    )

    recommendation = recommender.recommend(
        DecisionQuery(
            decision="charge_battery",
        )
    )

    assert recommendation is not None
    assert recommendation.decision == "charge_battery"
    assert recommendation.confidence == 2 / 3


def test_recommendation_confidence_is_bounded():
    memory = DecisionMemory()

    for index in range(5):
        memory.add(
            make_record(
                command_id=f"cmd-{index}",
                decision="charge_battery",
                success=True,
            )
        )

    recommender = DecisionMemoryRecommender(
        query=DecisionMemoryQuery(memory),
        ranker=DecisionMemoryRanker(),
    )

    recommendation = recommender.recommend(
        DecisionQuery()
    )

    assert recommendation is not None
    assert 0.0 <= recommendation.confidence <= 1.0
    assert recommendation.confidence == 1.0


def test_no_memory_produces_no_recommendation():
    memory = DecisionMemory()

    recommender = DecisionMemoryRecommender(
        query=DecisionMemoryQuery(memory),
        ranker=DecisionMemoryRanker(),
    )

    recommendation = recommender.recommend(
        DecisionQuery()
    )

    assert recommendation is None