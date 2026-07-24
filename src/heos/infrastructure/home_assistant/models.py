"""Home Assistant bridge models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class HomeAssistantEntityState:
    entity_id: str
    state: str
    attributes: Mapping[str, object] = field(default_factory=dict)
    last_updated: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def as_float(self) -> float | None:
        try:
            return float(self.state)
        except (TypeError, ValueError):
            return None

    def as_bool(self) -> bool | None:
        normalized = self.state.strip().lower()
        if normalized in {"on", "true", "yes", "connected", "charging"}:
            return True
        if normalized in {"off", "false", "no", "disconnected", "idle"}:
            return False
        return None


@dataclass(frozen=True, slots=True)
class EntityMap:
    """HEOS semantic names mapped to Home Assistant entity IDs."""

    pv_power: str
    house_power: str
    grid_power: str
    ev_soc: str | None = None
    ev_connected: str | None = None
    charger_power: str | None = None
    charger_current: str | None = None
    charger_enabled: str | None = None
    outdoor_temperature: str | None = None
    electricity_price: str | None = None


@dataclass(frozen=True, slots=True)
class RawEnergySnapshot:
    """Transport-neutral snapshot collected from Home Assistant."""

    pv_power_w: float
    house_power_w: float
    grid_power_w: float
    ev_soc_percent: float | None
    ev_connected: bool | None
    charger_power_w: float | None
    charger_current_a: float | None
    charger_enabled: bool | None
    outdoor_temperature_c: float | None
    electricity_price_eur_kwh: float | None
    collected_at: datetime
    source_entities: Mapping[str, str]

    @property
    def grid_import_w(self) -> float:
        return max(self.grid_power_w, 0.0)

    @property
    def grid_export_w(self) -> float:
        return max(-self.grid_power_w, 0.0)

    @property
    def solar_surplus_w(self) -> float:
        return self.grid_export_w
