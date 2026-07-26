from datetime import UTC, datetime

import pytest

from heos.result_verification.context_decision_recommendation import (
    ContextAwareDecisionRecommender,
)
from heos.result_verification.context_similarity import (
    ContextSimilarityEngine,
)
from heos.result_verification.decision_context import (
    DecisionContext,
    DecisionContextMemory,
)
from heos.result_verification.decision_memory import (
    DecisionMemory,
    DecisionMemoryRecord,
)


def add_memory(
    memory: DecisionMemory,
    *,
    command_id: str,
    decision: str,
    success: bool,
) -> None:
    memory.add(
        DecisionMemoryRecord(
            command_id=command_id,
            decision=decision,
            outcome="SUCCESS" if success else "FAILED",
            expected_value=5000.0,
            actual_value=4900.0 if success else 3500.0,
            success=success,
            created_at=datetime.now(UTC),
        )
    )


def make_recommender() -> ContextAwareDecisionRecommender:
    context_memory = DecisionContextMemory()

    context_memory.add(
        DecisionContext(
            decision="charge_battery",
            context={
                "pv_surplus": True,
                "battery_soc": "low",
                "tariff": "high",
            },
        )
    )

    context_memory.add(
        DecisionContext(
            decision="reduce_charging",
            context={
                "pv_surplus": False,
                "battery_soc": "high",
                "tariff": "high",
            },
        )
    )

    decision_memory = DecisionMemory()

    add_memory(
        decision_memory,
        command_id="cmd-001",
        decision="charge_battery",
        success=True,
    )
    add_memory(
        decision_memory,
        command_id="cmd-002",
        decision="charge_battery",
        success=True,
    )

    add_memory(
        decision_memory,
        command_id="cmd-003",
        decision="reduce_charging",
        success=True,
    )
    add_memory(
        decision_memory,
        command_id="cmd-004",
        decision="reduce_charging",
        success=True,
    )

    return ContextAwareDecisionRecommender(
        context_memory=context_memory,
        decision_memory=decision_memory,
        similarity_engine=ContextSimilarityEngine(),
        minimum_similarity=0.5,
    )


def test_current_context_selects_matching_past_decision():
    recommender = make_recommender()

    recommendation = recommender.recommend(
        {
            "pv_surplus": True,
            "battery_soc": "low",
            "tariff": "high",
        }
    )

    assert recommendation is not None
    assert recommendation.decision == "charge_battery"
    assert recommendation.confidence == 1.0


def test_different_context_changes_recommendation():
    recommender = make_recommender()

    recommendation = recommender.recommend(
        {
            "pv_surplus": False,
            "battery_soc": "high",
            "tariff": "high",
        }
    )

    assert recommendation is not None
    assert recommendation.decision == "reduce_charging"
    assert recommendation.confidence == 1.0


def test_failed_history_reduces_contextual_confidence():
    context_memory = DecisionContextMemory()

    context_memory.add(
        DecisionContext(
            decision="charge_battery",
            context={
                "pv_surplus": True,
                "battery_soc": "low",
            },
        )
    )

    decision_memory = DecisionMemory()

    add_memory(
        decision_memory,
        command_id="cmd-001",
        decision="charge_battery",
        success=True,
    )
    add_memory(
        decision_memory,
        command_id="cmd-002",
        decision="charge_battery",
        success=False,
    )

    recommender = ContextAwareDecisionRecommender(
        context_memory=context_memory,
        decision_memory=decision_memory,
        similarity_engine=ContextSimilarityEngine(),
    )

    recommendation = recommender.recommend(
        {
            "pv_surplus": True,
            "battery_soc": "low",
        }
    )

    assert recommendation is not None
    assert recommendation.decision == "charge_battery"
    assert recommendation.confidence == 0.5


def test_unrelated_context_produces_no_recommendation():
    recommender = make_recommender()

    recommendation = recommender.recommend(
        {
            "pv_surplus": "unknown",
            "battery_soc": "medium",
            "tariff": "low",
        }
    )

    assert recommendation is None


def test_empty_context_is_rejected():
    recommender = make_recommender()

    with pytest.raises(ValueError):
        recommender.recommend({})


def test_similarity_threshold_must_be_bounded():
    with pytest.raises(ValueError):
        ContextAwareDecisionRecommender(
            context_memory=DecisionContextMemory(),
            decision_memory=DecisionMemory(),
            similarity_engine=ContextSimilarityEngine(),
            minimum_similarity=1.1,
        )