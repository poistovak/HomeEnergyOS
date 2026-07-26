from datetime import UTC, datetime

import pytest

from heos.result_verification import LearningRecord


def make_record():
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=5000.0,
        actual_value=4800.0,
        success=True,
        timestamp=datetime.now(UTC),
    )


def test_learning_record_accepts_valid_values():
    record = make_record()

    assert record.prediction_id == "pred-001"
    assert record.success is True


def test_learning_record_requires_prediction_id():
    with pytest.raises(ValueError):
        LearningRecord(
            prediction_id="",
            command_id="cmd-001",
            expected_value=1.0,
            actual_value=1.0,
            success=True,
            timestamp=datetime.now(),
        )


def test_learning_record_requires_command_id():
    with pytest.raises(ValueError):
        LearningRecord(
            prediction_id="pred-001",
            command_id="",
            expected_value=1.0,
            actual_value=1.0,
            success=True,
            timestamp=datetime.now(UTC),
        )


def test_learning_record_requires_timezone():
    with pytest.raises(ValueError):
        LearningRecord(
            prediction_id="pred-001",
            command_id="cmd-001",
            expected_value=1.0,
            actual_value=1.0,
            success=True,
            timestamp=datetime.now(),
        )