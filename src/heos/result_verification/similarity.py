from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class LearningSimilarity:
    expected_value_delta: float
    success_match: bool = False

    def matches(
        self,
        record: LearningRecord,
        expected_value: float,
    ) -> bool:
        if abs(
            record.expected_value - expected_value
        ) > self.expected_value_delta:
            return False

        return not (self.success_match and not record.success)