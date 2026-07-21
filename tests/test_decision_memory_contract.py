from datetime import datetime, timezone

from heos.result_verification import (
    DecisionMemory,
    DecisionMemoryRecord,
)


def test_memory_stores_decision():

    memory = DecisionMemory()

    record = DecisionMemoryRecord(
        command_id="cmd-080",
        decision="increase charging power",
        outcome="SUCCESS",
        expected_value=3000.0,
        actual_value=2980.0,
        success=True,
        created_at=datetime.now(timezone.utc),
    )

    memory.add(record)

    result = memory.find("cmd-080")

    assert len(result) == 1
    assert result[0].success is True