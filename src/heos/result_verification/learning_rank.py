from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class LearningRank:
    expected_value: float

    def score(
        self,
        record: LearningRecord,
    ) -> float:
        error = abs(
            record.expected_value - self.expected_value
        )

        success_bonus = 1.0 if record.success else 0.0

        return success_bonus - error