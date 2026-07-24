from __future__ import annotations

from dataclasses import dataclass

from .learning import LearningRecord


@dataclass(frozen=True, slots=True)
class LearningQuery:
    command_id: str | None = None
    prediction_id: str | None = None
    success: bool | None = None

    def matches(
        self,
        record: LearningRecord,
    ) -> bool:
        if self.command_id is not None and record.command_id != self.command_id:
            return False

        if self.prediction_id is not None and record.prediction_id != self.prediction_id:
            return False

        return not (self.success is not None and record.success != self.success)