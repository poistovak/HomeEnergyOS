"""Core decision model for HEOS.

Every decision must have a reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class Action(StrEnum):
    CHARGE = "charge"
    PREPARE = "prepare"
    WAIT = "wait"
    STOP = "stop"
    HEAT_WATER = "heat_water"
    PRECOOL = "precool"
    EXPORT = "export"


@dataclass(frozen=True, slots=True)
class DecisionReason:
    code: str
    message: str
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class Decision:
    action: Action
    confidence: float
    reasons: tuple[DecisionReason, ...]
    parameters: dict[str, Any] = field(default_factory=dict)
    valid_for: timedelta = timedelta(seconds=60)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decision_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not self.reasons:
            raise ValueError("every decision must have at least one reason")
        if self.valid_for <= timedelta(0):
            raise ValueError("valid_for must be positive")

    @property
    def expires_at(self) -> datetime:
        return self.created_at + self.valid_for

    def is_expired(self, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) >= self.expires_at

    def explain(self) -> str:
        return " ".join(reason.message for reason in self.reasons)
