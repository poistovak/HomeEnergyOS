from heos.result_verification import (
    PatternMemory,
    PatternMemoryRecord,
)


def test_pattern_memory_stores_records():

    memory = PatternMemory()

    record = PatternMemoryRecord(
        pattern="charge_when_surplus",
        success_rate=0.95,
    )

    memory.add(record)

    result = memory.all()

    assert len(result) == 1
    assert result[0].pattern == "charge_when_surplus"
    assert result[0].success_rate == 0.95