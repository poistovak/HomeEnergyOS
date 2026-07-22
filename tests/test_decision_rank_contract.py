from datetime import datetime, timezone

from heos.result_verification import (
    DecisionMemoryRanker,
    DecisionMemoryRecord,
)


def make_record(success):

    return DecisionMemoryRecord(
        command_id="cmd-083",
        decision="charge",
        outcome="SUCCESS",
        expected_value=5000,
        actual_value=4900,
        success=success,
        created_at=datetime.now(timezone.utc),
    )


def test_rank_success_first():

    ranker = DecisionMemoryRanker()

    result = ranker.rank(
        [
            make_record(False),
            make_record(True),
        ]
    )

    assert result[0].record.success is True