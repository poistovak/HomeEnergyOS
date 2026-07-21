from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class LearningRecord:
    prediction_id: str
    command_id: str
    expected_value: float
    actual_value: float
    success: bool
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.prediction_id.strip():
            raise ValueError(
                "prediction_id must not be empty"
            )

        if not self.command_id.strip():
            raise ValueError(
                "command_id must not be empty"
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware"
            )