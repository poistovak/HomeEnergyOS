"""Small deterministic trend estimator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean
from typing import Sequence


class TrendDirection(StrEnum):
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Trend:
    direction: TrendDirection
    slope_per_step: float
    confidence: float
    samples: int


class TrendEstimator:
    """Estimate a linear trend without third-party numerical libraries."""

    def estimate(
        self,
        values: Sequence[float],
        *,
        stable_tolerance: float = 50.0,
    ) -> Trend:
        count = len(values)
        if count < 2:
            return Trend(
                direction=TrendDirection.UNKNOWN,
                slope_per_step=0.0,
                confidence=0.0,
                samples=count,
            )

        x_mean = (count - 1) / 2.0
        y_mean = fmean(values)
        denominator = sum((index - x_mean) ** 2 for index in range(count))
        numerator = sum(
            (index - x_mean) * (value - y_mean)
            for index, value in enumerate(values)
        )
        slope = numerator / denominator if denominator else 0.0

        if abs(slope) <= stable_tolerance:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.RISING
        else:
            direction = TrendDirection.FALLING

        spread = max(values) - min(values)
        if spread == 0:
            confidence = 1.0
        else:
            explained = min(abs(slope) * max(count - 1, 1) / spread, 1.0)
            confidence = max(0.25, explained)

        return Trend(
            direction=direction,
            slope_per_step=slope,
            confidence=confidence,
            samples=count,
        )
