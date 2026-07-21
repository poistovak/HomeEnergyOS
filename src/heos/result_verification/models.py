from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import math


class VerificationStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"


class VerificationAction(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


@dataclass(frozen=True, slots=True)
class Observation:
    target: str
    value: float
    observed_at: datetime
    source: str
    quality: float = 1.0

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError("target must not be empty")

        if not self.source.strip():
            raise ValueError("source must not be empty")

        if not math.isfinite(self.value):
            raise ValueError("value must be finite")

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware"
            )

        if not 0.0 <= self.quality <= 1.0:
            raise ValueError(
                "quality must be between 0 and 1"
            )


@dataclass(frozen=True, slots=True)
class ResultExpectation:
    prediction_id: str
    expected_value: float
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.prediction_id.strip():
            raise ValueError(
                "prediction_id must not be empty"
            )

        if not math.isfinite(self.expected_value):
            raise ValueError(
                "expected_value must be finite"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    prediction_id: str
    passed: bool
    absolute_error: float
    relative_error: float

    def __post_init__(self) -> None:
        if not self.prediction_id.strip():
            raise ValueError(
                "prediction_id must not be empty"
            )

        if self.absolute_error < 0:
            raise ValueError(
                "absolute_error must be non-negative"
            )

        if self.relative_error < 0:
            raise ValueError(
                "relative_error must be non-negative"
            )