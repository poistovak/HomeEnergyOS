from datetime import UTC, datetime

from heos.result_verification import (
    LearningRecord,
    LearningSimilarity,
)


def make_record():
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=5000.0,
        actual_value=4900.0,
        success=True,
        timestamp=datetime.now(UTC),
    )


def test_similarity_accepts_close_value():
    similarity = LearningSimilarity(
        expected_value_delta=200.0,
    )

    assert similarity.matches(
        make_record(),
        5100.0,
    )


def test_similarity_rejects_far_value():
    similarity = LearningSimilarity(
        expected_value_delta=100.0,
    )

    assert not similarity.matches(
        make_record(),
        6000.0,
    )


def test_similarity_checks_success():
    similarity = LearningSimilarity(
        expected_value_delta=200.0,
        success_match=True,
    )

    assert similarity.matches(
        make_record(),
        5000.0,
    )