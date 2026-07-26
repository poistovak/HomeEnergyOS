from datetime import UTC, datetime

import pytest

from heos.result_verification.context_similarity import (
    ContextSimilarityEngine,
)
from heos.result_verification.decision_experience import (
    DecisionExperience,
    DecisionExperienceMemory,
)
from heos.result_verification.experience_reasoner import (
    ExperienceReasoner,
)
from heos.result_verification.reasoning_confidence import (
    ReasoningConfidenceEngine,
)
from heos.result_verification.reasoning_orchestrator import (
    ReasoningOrchestrator,
)
from heos.result_verification.weighted_evidence import (
    WeightedEvidenceEngine,
)


def add_experience(
    memory: DecisionExperienceMemory,
    *,
    command_id: str,
    decision: str,
    context: dict[str, object],
    success: bool,
) -> None:
    memory.add(
        DecisionExperience(
            command_id=command_id,
            decision=decision,
            context=context,
            outcome="SUCCESS" if success else "FAILED",
            expected_value=5000.0,
            actual_value=4900.0 if success else 3200.0,
            success=success,
            created_at=datetime.now(UTC),
        )
    )


def make_reasoner(
    memory: DecisionExperienceMemory,
) -> ExperienceReasoner:
    return ExperienceReasoner(
        memory=memory,
        similarity_engine=ContextSimilarityEngine(),
        evidence_engine=WeightedEvidenceEngine(),
        confidence_engine=ReasoningConfidenceEngine(),
        orchestrator=ReasoningOrchestrator(),
        minimum_similarity=0.5,
    )


def test_reasoner_selects_decision_supported_by_contextual_experience():
    memory = DecisionExperienceMemory()

    add_experience(
        memory,
        command_id="cmd-001",
        decision="charge_battery",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=True,
    )

    add_experience(
        memory,
        command_id="cmd-002",
        decision="reduce_charging",
        context={
            "pv_surplus": False,
            "battery_soc": "high",
        },
        success=True,
    )

    result = make_reasoner(memory).reason(
        {
            "pv_surplus": True,
            "battery_soc": "low",
        }
    )

    assert result is not None
    assert result.decision == "charge_battery"
    assert result.confidence == 1.0


def test_reasoner_uses_weighted_failed_experience():
    memory = DecisionExperienceMemory()

    add_experience(
        memory,
        command_id="cmd-001",
        decision="charge_battery",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=True,
    )

    add_experience(
        memory,
        command_id="cmd-002",
        decision="charge_battery",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=False,
    )

    result = make_reasoner(memory).reason(
        {
            "pv_surplus": True,
            "battery_soc": "low",
        }
    )

    assert result is not None
    assert result.decision == "charge_battery"
    assert result.confidence == pytest.approx(0.5)


def test_reasoner_prefers_stronger_evidence():
    memory = DecisionExperienceMemory()

    add_experience(
        memory,
        command_id="cmd-001",
        decision="charge_battery",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=True,
    )

    add_experience(
        memory,
        command_id="cmd-002",
        decision="reduce_charging",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=False,
    )

    result = make_reasoner(memory).reason(
        {
            "pv_surplus": True,
            "battery_soc": "low",
        }
    )

    assert result is not None
    assert result.decision == "charge_battery"
    assert result.confidence == 1.0


def test_reasoner_returns_none_without_relevant_experience():
    memory = DecisionExperienceMemory()

    add_experience(
        memory,
        command_id="cmd-001",
        decision="charge_battery",
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        success=True,
    )

    result = make_reasoner(memory).reason(
        {
            "pv_surplus": False,
            "battery_soc": "high",
        }
    )

    assert result is None


def test_reasoner_rejects_empty_context():
    memory = DecisionExperienceMemory()

    with pytest.raises(ValueError):
        make_reasoner(memory).reason({})


def test_reasoner_requires_valid_similarity_threshold():
    with pytest.raises(ValueError):
        ExperienceReasoner(
            memory=DecisionExperienceMemory(),
            similarity_engine=ContextSimilarityEngine(),
            evidence_engine=WeightedEvidenceEngine(),
            confidence_engine=ReasoningConfidenceEngine(),
            orchestrator=ReasoningOrchestrator(),
            minimum_similarity=1.1,
        )