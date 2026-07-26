from datetime import UTC, datetime, timedelta

from heos.result_verification.learning import LearningRecord
from heos.result_verification.learning_similarity import LearningSimilarity
from heos.result_verification.memory import LearningMemory
from heos.result_verification.retrieval import LearningRetrieval


def make_record(
    prediction_id: str,
    command_id: str,
    expected_value: float,
    actual_value: float,
    success: bool,
    *,
    seconds: int = 0,
) -> LearningRecord:
    return LearningRecord(
        prediction_id=prediction_id,
        command_id=command_id,
        expected_value=expected_value,
        actual_value=actual_value,
        success=success,
        timestamp=datetime.now(UTC) + timedelta(seconds=seconds),
    )


def test_retrieval_finds_similar_successful_experience():
    memory = LearningMemory()

    relevant = make_record(
        "pred-001",
        "cmd-001",
        5000.0,
        4900.0,
        True,
    )

    distant = make_record(
        "pred-002",
        "cmd-002",
        8000.0,
        7900.0,
        True,
    )

    memory.add(relevant)
    memory.add(distant)

    retrieval = LearningRetrieval(memory)

    results = retrieval.find_similar(
        expected_value=5100.0,
        similarity=LearningSimilarity(
            expected_value_delta=250.0,
        ),
    )

    assert results == (relevant,)


def test_retrieval_ignores_failed_experience_by_default():
    memory = LearningMemory()

    successful = make_record(
        "pred-success",
        "cmd-success",
        5000.0,
        4950.0,
        True,
    )

    failed = make_record(
        "pred-failed",
        "cmd-failed",
        5050.0,
        3000.0,
        False,
    )

    memory.add(successful)
    memory.add(failed)

    retrieval = LearningRetrieval(memory)

    results = retrieval.find_similar(
        expected_value=5000.0,
        similarity=LearningSimilarity(
            expected_value_delta=100.0,
        ),
    )

    assert results == (successful,)


def test_retrieval_can_include_failed_experience():
    memory = LearningMemory()

    successful = make_record(
        "pred-success",
        "cmd-success",
        5000.0,
        4950.0,
        True,
    )

    failed = make_record(
        "pred-failed",
        "cmd-failed",
        5050.0,
        3000.0,
        False,
    )

    memory.add(successful)
    memory.add(failed)

    retrieval = LearningRetrieval(memory)

    results = retrieval.find_similar(
        expected_value=5000.0,
        similarity=LearningSimilarity(
            expected_value_delta=100.0,
            success_match=False,
        ),
    )

    assert results == (
        successful,
        failed,
    )


def test_retrieval_returns_empty_when_no_experience_matches():
    memory = LearningMemory()

    memory.add(
        make_record(
            "pred-001",
            "cmd-001",
            5000.0,
            4900.0,
            True,
        )
    )

    retrieval = LearningRetrieval(memory)

    results = retrieval.find_similar(
        expected_value=9000.0,
        similarity=LearningSimilarity(
            expected_value_delta=100.0,
        ),
    )

    assert results == ()