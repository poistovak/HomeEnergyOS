from datetime import datetime, timezone

from heos.result_verification import (
    LearningMemory,
    LearningRecord,
)


def record():
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=5000.0,
        actual_value=4900.0,
        success=True,
        timestamp=datetime.now(timezone.utc),
    )


def test_memory_accepts_record():
    memory = LearningMemory()

    memory.add(record())

    assert memory.count() == 1


def test_memory_returns_records():
    memory = LearningMemory()

    item = record()
    memory.add(item)

    assert memory.all() == (item,)


def test_latest_returns_last_record():
    memory = LearningMemory()

    first = record()
    second = record()

    memory.add(first)
    memory.add(second)

    assert memory.latest() == second


def test_empty_memory_returns_none():
    memory = LearningMemory()

    assert memory.latest() is None