from datetime import UTC, datetime

import pytest

from heos.result_verification.decision_experience import (
    DecisionExperience,
    DecisionExperienceMemory,
)


def make_experience(
    *,
    decision: str = "charge_battery",
    success: bool = True,
) -> DecisionExperience:
    return DecisionExperience(
        command_id="cmd-001",
        decision=decision,
        context={
            "pv_surplus": True,
            "battery_soc": "low",
        },
        outcome="target_reached" if success else "target_not_reached",
        expected_value=5000.0,
        actual_value=4900.0 if success else 3200.0,
        success=success,
        created_at=datetime.now(UTC),
    )


def test_experience_preserves_decision_context_and_result():
    experience = make_experience()

    assert experience.command_id == "cmd-001"
    assert experience.decision == "charge_battery"
    assert experience.context["pv_surplus"] is True
    assert experience.expected_value == 5000.0
    assert experience.actual_value == 4900.0
    assert experience.success is True


def test_experience_memory_stores_experience():
    memory = DecisionExperienceMemory()

    experience = make_experience()

    memory.add(experience)

    assert memory.count() == 1
    assert memory.all() == (experience,)


def test_memory_filters_by_decision():
    memory = DecisionExperienceMemory()

    charge = make_experience(
        decision="charge_battery",
    )

    reduce = make_experience(
        decision="reduce_charging",
    )

    memory.add(charge)
    memory.add(reduce)

    assert memory.for_decision(
        "charge_battery"
    ) == (charge,)


def test_experience_requires_context():
    with pytest.raises(ValueError):
        DecisionExperience(
            command_id="cmd-001",
            decision="charge_battery",
            context={},
            outcome="target_reached",
            expected_value=5000.0,
            actual_value=4900.0,
            success=True,
            created_at=datetime.now(UTC),
        )


def test_experience_requires_decision():
    with pytest.raises(ValueError):
        DecisionExperience(
            command_id="cmd-001",
            decision="",
            context={
                "pv_surplus": True,
            },
            outcome="target_reached",
            expected_value=5000.0,
            actual_value=4900.0,
            success=True,
            created_at=datetime.now(UTC),
        )