from datetime import datetime, timezone

from heos.result_verification import (
    LearningRank,
    LearningRecord,
)


def make_record(value, success=True):
    return LearningRecord(
        prediction_id="pred-001",
        command_id="cmd-001",
        expected_value=value,
        actual_value=value - 50,
        success=success,
        timestamp=datetime.now(timezone.utc),
    )


def test_rank_prefers_closer_success():
    rank = LearningRank(
        expected_value=5000.0,
    )

    good = make_record(5000.0)
    far = make_record(7000.0)

    assert rank.score(good) > rank.score(far)


def test_rank_rewards_success():
    rank = LearningRank(
        expected_value=5000.0,
    )

    success = make_record(5000.0, True)
    failed = make_record(5000.0, False)

    assert rank.score(success) > rank.score(failed)


def test_rank_returns_number():
    rank = LearningRank(
        expected_value=5000.0,
    )

    assert isinstance(
        rank.score(make_record(5000.0)),
        float,
    )