from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .learning import LearningRecord
from .models import (
    ResultExpectation,
    VerificationDecision,
    VerificationStatus,
)


@dataclass(frozen=True, slots=True)
class LearningBridge:
    """
    Converts verified reality into a learning record.
    """

    def build_record(
        self,
        *,
        prediction_id: str,
        expectation: ResultExpectation,
        decision: VerificationDecision,
        timestamp: datetime,
    ) -> LearningRecord | None:
        if not prediction_id.strip():
            raise ValueError("prediction_id must not be empty")

        if timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        if decision.command_id != expectation.command_id:
            raise ValueError(
                "decision command_id does not match expectation"
            )

        if decision.target != expectation.target:
            raise ValueError(
                "decision target does not match expectation"
            )

        if decision.expected_value != expectation.expected_value:
            raise ValueError(
                "decision expected_value does not match expectation"
            )

        if decision.observed_value is None:
            return None

        return LearningRecord(
            prediction_id=prediction_id,
            command_id=decision.command_id,
            expected_value=decision.expected_value,
            actual_value=decision.observed_value,
            success=decision.status is VerificationStatus.SUCCESS,
            timestamp=timestamp,
        )