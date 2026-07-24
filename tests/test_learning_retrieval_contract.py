from datetime import UTC, datetime

from heos.result_verification import (
    LearningMemory,
    LearningRecord,
    LearningRetrieval,
    LearningSimilarity,
)


def make_record(value):
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=value,
        actual_value=value - 50,
        success=True,
        timestamp=datetime.now(UTC),
    )


def test_retrieval_finds_similar_records():
    memory = LearningMemory()

    memory.add(make_record(5000.0))
    memory.add(make_record(8000.0))

    retrieval = LearningRetrieval(memory)

    result = retrieval.find_similar(
        expected_value=5100.0,
        similarity=LearningSimilarity(
            expected_value_delta=200.0,
        ),
    )

    assert len(result) == 1
    assert result[0].expected_value == 5000.0


def test_retrieval_returns_empty_when_no_match():
    memory = LearningMemory()

    memory.add(make_record(5000.0))

    retrieval = LearningRetrieval(memory)

    result = retrieval.find_similar(
        expected_value=9000.0,
        similarity=LearningSimilarity(
            expected_value_delta=100.0,
        ),
    )

    assert result == ()


def test_retrieval_uses_existing_memory():
    memory = LearningMemory()

    item = make_record(3000.0)
    memory.add(item)

    retrieval = LearningRetrieval(memory)

    result = retrieval.find_similar(
        expected_value=3000.0,
        similarity=LearningSimilarity(
            expected_value_delta=1.0,
        ),
    )

    assert result[0] == item