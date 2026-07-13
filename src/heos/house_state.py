"""Unified HEOS HouseState."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Mapping
from .twin import DigitalTwin

class ControlMode(StrEnum):
    RECOMMENDATION = "recommendation"
    SEMI_AUTOMATIC = "semi_automatic"
    AUTOPILOT = "autopilot"

class Objective(StrEnum):
    SELF_CONSUMPTION = "self_consumption"
    LOWEST_COST = "lowest_cost"
    COMFORT = "comfort"
    GRID_FRIENDLY = "grid_friendly"
    BALANCED = "balanced"

@dataclass(frozen=True, slots=True)
class UserIntent:
    control_mode: ControlMode = ControlMode.RECOMMENDATION
    objective: Objective = Objective.BALANCED
    ev_target_soc_percent: float = 80.0
    ev_ready_by: datetime | None = None
    allow_grid_charging: bool = False
    allow_export: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.ev_target_soc_percent <= 100.0:
            raise ValueError("ev_target_soc_percent must be between 0 and 100")

@dataclass(frozen=True, slots=True)
class SafetyConstraints:
    main_breaker_a: float = 25.0
    phases: int = 3
    maximum_grid_import_w: float | None = None
    maximum_grid_export_w: float | None = None
    minimum_home_battery_soc_percent: float | None = None
    minimum_ev_current_a: float = 6.0
    maximum_ev_current_a: float = 16.0

    def __post_init__(self) -> None:
        if self.main_breaker_a <= 0:
            raise ValueError("main_breaker_a must be positive")
        if self.phases not in {1, 2, 3}:
            raise ValueError("phases must be 1, 2 or 3")
        if self.maximum_ev_current_a < self.minimum_ev_current_a:
            raise ValueError("maximum_ev_current_a must be >= minimum_ev_current_a")

@dataclass(frozen=True, slots=True)
class PredictionWindow:
    pv_next_15m_w: float | None = None
    pv_next_60m_w: float | None = None
    household_next_60m_w: float | None = None
    electricity_price_next_hour_eur_kwh: float | None = None
    expected_cloud_risk_percent: float | None = None

@dataclass(frozen=True, slots=True)
class OperatingPolicy:
    reserve_power_w: float = 250.0
    decision_validity_seconds: int = 45
    minimum_confidence_for_action: float = 0.80
    minimum_stable_surplus_seconds: int = 120
    prefer_local_energy: bool = True

@dataclass(frozen=True, slots=True)
class HouseState:
    twin: DigitalTwin
    intent: UserIntent = field(default_factory=UserIntent)
    constraints: SafetyConstraints = field(default_factory=SafetyConstraints)
    predictions: PredictionWindow = field(default_factory=PredictionWindow)
    policy: OperatingPolicy = field(default_factory=OperatingPolicy)
    tags: Mapping[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def can_execute_automatically(self) -> bool:
        return (
            self.intent.control_mode is ControlMode.AUTOPILOT
            and self.twin.usable_for_autopilot
        )

    @property
    def decision_ready(self) -> bool:
        return (
            self.twin.power.quality.confidence >= self.policy.minimum_confidence_for_action
            and self.twin.power.quality.age_seconds <= 60
        )

    def summary(self) -> dict[str, object]:
        return {
            "control_mode": self.intent.control_mode.value,
            "objective": self.intent.objective.value,
            "decision_ready": self.decision_ready,
            "can_execute_automatically": self.can_execute_automatically,
            "main_breaker_a": self.constraints.main_breaker_a,
            "phases": self.constraints.phases,
            "ev_target_soc_percent": self.intent.ev_target_soc_percent,
            "reserve_power_w": self.policy.reserve_power_w,
            "twin": self.twin.summary(),
        }
