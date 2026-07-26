from datetime import UTC, datetime

import pytest

from heos.result_verification.decision_memory_bridge import DecisionMemoryBridge
from heos.result_verification.learning import LearningRecord


def make_learning_record() -> LearningRecord:
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=5000.0,
        actual_value=4900.0,
        success=True,
        timestamp=datetime.now(UTC),
    )


def test_bridge_creates_decision_memory_record():
    bridge = DecisionMemoryBridge()

    record = bridge.build_record(
        learning=make_learning_record(),
        decision="charge_battery",
        outcome="pv_surplus_absorbed",
    )

    assert record.command_id == "cmd-001"
    assert record.decision == "charge_battery"
    assert record.outcome == "pv_surplus_absorbed"
    assert record.expected_value == 5000.0
    assert record.actual_value == 4900.0
    assert record.success is True


def test_bridge_preserves_learning_timestamp():
    learning = make_learning_record()
    bridge = DecisionMemoryBridge()

    record = bridge.build_record(
        learning=learning,
        decision="charge_battery",
        outcome="pv_surplus_absorbed",
    )

    assert record.created_at == learning.timestamp


def test_bridge_preserves_failed_experience():
    learning = LearningRecord(
        prediction_id="pred-002",
        command_id="cmd-002",
        expected_value=5000.0,
        actual_value=3200.0,
        success=False,
        timestamp=datetime.now(UTC),
    )

    bridge = DecisionMemoryBridge()

    record = bridge.build_record(
        learning=learning,
        decision="charge_battery",
        outcome="target_not_reached",
    )

    assert record.success is False
    assert record.actual_value == 3200.0


def test_bridge_requires_decision():
    bridge = DecisionMemoryBridge()

    with pytest.raises(ValueError):
        bridge.build_record(
            learning=make_learning_record(),
            decision="",
            outcome="pv_surplus_absorbed",
        )


def test_bridge_requires_outcome():
    bridge = DecisionMemoryBridge()

    with pytest.raises(ValueError):
        bridge.build_record(
            learning=make_learning_record(),
            decision="charge_battery",
            outcome="",
        )