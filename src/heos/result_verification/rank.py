from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class LearningRank:
    expected_value: float

    def score(self, record: LearningRecord) -> float:
        error = abs(
            record.actual_value - self.expected_value
        )

        accuracy = 1.0 / (1.0 + error)

        if record.success:
            return float(accuracy + 1.0)

        return float(accuracy)