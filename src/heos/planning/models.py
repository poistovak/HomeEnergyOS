"""Immutable future scenario models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True, slots=True)
class PlannedAction:
    action_id: str
    target_resource_id: str | None
    parameters: Mapping[str, object] = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ScenarioMetrics:
    expected_cost_eur: float = 0.0
    expected_grid_import_kwh: float = 0.0
    expected_grid_export_kwh: float = 0.0
    expected_self_consumption_percent: float = 0.0
    expected_ev_energy_kwh: float = 0.0
    expected_storage_wear: float = 0.0
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.expected_self_consumption_percent <= 100.0:
            raise ValueError(
                "expected_self_consumption_percent must be between 0 and 100"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class FutureScenario:
    scenario_id: str
    title: str
    actions: tuple[PlannedAction, ...]
    metrics: ScenarioMetrics
    score: float
    reasons: tuple[str, ...]
    horizon: timedelta = timedelta(minutes=15)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def executable(self) -> bool:
        return bool(self.actions)
