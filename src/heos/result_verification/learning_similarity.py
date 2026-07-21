from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class LearningSimilarity:
    expected_value_delta: float
    success_match: bool = True

    def matches(
        self,
        record: LearningRecord,
        expected_value: float,
    ) -> bool:
        value_close = (
            abs(
                record.expected_value - expected_value
            )
            <= self.expected_value_delta
        )

        if not value_close:
            return False

        if self.success_match:
            return record.success

        return True