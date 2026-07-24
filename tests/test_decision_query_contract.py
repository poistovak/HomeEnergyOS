from datetime import UTC, datetime

from heos.result_verification import (
    DecisionMemory,
    DecisionMemoryQuery,
    DecisionMemoryRecord,
    DecisionQuery,
)


def make_record(success=True):

    return DecisionMemoryRecord(
        command_id="cmd-082",
        decision="increase_power",
        outcome="SUCCESS",
        expected_value=3000,
        actual_value=2950,
        success=success,
        created_at=datetime.now(UTC),
    )


def test_query_finds_successful_decisions():

    memory = DecisionMemory()

    memory.add(make_record(True))
    memory.add(make_record(False))

    query = DecisionMemoryQuery(memory)

    result = query.search(
        DecisionQuery(
            decision="increase_power",
            success_only=True,
        )
    )

    assert len(result) == 1
    assert result[0].success is True