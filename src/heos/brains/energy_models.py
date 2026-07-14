"""Immutable output models for the HEOS whole-home decision brain."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EnergyAction(StrEnum):
    """Vendor-independent actions proposed by the decision brain."""

    HOLD = "hold"
    CHARGE_EV = "charge_ev"
    STOP_EV_CHARGING = "stop_ev_charging"
    EXPORT_SURPLUS = "export_surplus"


@dataclass(frozen=True, slots=True)
class DecisionReason:
    """One human-readable reason supporting a decision."""

    code: str
    message: str
    weight: float

    def __post_init__(self) -> None:
        if not -1.0 <= self.weight <= 1.0:
            raise ValueError("weight must be between -1.0 and 1.0")


@dataclass(frozen=True, slots=True)
class EnergyDecision:
    """Explainable decision produced from one immutable HouseState."""

    action: EnergyAction
    confidence: float
    score: float
    reasons: tuple[DecisionReason, ...]
    parameters: dict[str, Any] = field(default_factory=dict)
    brain_id: str = "home_energy"
    brain_version: str = "0.6.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decision_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def explain(self) -> str:
        lines = [
            f"Action: {self.action.value}",
            f"Confidence: {self.confidence:.0%}",
            f"Score: {self.score:.1f}",
            "Reasons:",
        ]
        lines.extend(f"- {reason.message}" for reason in self.reasons)
        return "\n".join(lines)
