from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import mathPredictionRealityComparison

- prediction_id
- predicted_value
- actual_value
- absolute_error
- relative_error
- timestamp
- metric_name
- passed
@dataclass(frozen=True, slots=True)
class PredictionRealityComparison:
    prediction_id: str
    predicted_value: float
    actual_value: float
    absolute_error: float
    relative_error: float
    timestamp: datetime
    metric_name: str
    passed: bool

    def __post_init__(self) -> None:
        if not self.prediction_id.strip():
            raise ValueError("prediction_id must not be empty")

        if not self.metric_name.strip():
            raise ValueError("metric_name must not be empty")

        values = (
            self.predicted_value,
            self.actual_value,
            self.absolute_error,
            self.relative_error,
        )

        if any(not math.isfinite(value) for value in values):
            raise ValueError("values must be finite")

        if self.absolute_error < 0:
            raise ValueError("absolute_error must be non-negative")

        if self.relative_error < 0:
            raise ValueError("relative_error must be non-negative")