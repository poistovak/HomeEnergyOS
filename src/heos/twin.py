"""Digital Twin models for HEOS.

The Digital Twin is a vendor-independent, immutable representation of the
current home energy system. Brains reason about this model, never about raw
Home Assistant entity IDs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Mapping


class Availability(StrEnum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class OperatingMode(StrEnum):
    IDLE = "idle"
    ACTIVE = "active"
    CHARGING = "charging"
    HEATING = "heating"
    COOLING = "cooling"
    EXPORTING = "exporting"
    IMPORTING = "importing"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SourceQuality:
    """Quality metadata attached to normalized measurements."""

    confidence: float = 1.0
    age_seconds: float = 0.0
    source: str = "unknown"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.age_seconds < 0:
            raise ValueError("age_seconds must not be negative")


@dataclass(frozen=True, slots=True)
class PowerFlow:
    """Instantaneous power balance in watts."""

    pv_w: float
    house_w: float
    grid_w: float
    battery_w: float = 0.0
    ev_w: float = 0.0
    heat_pump_w: float = 0.0
    quality: SourceQuality = field(default_factory=SourceQuality)

    @property
    def grid_import_w(self) -> float:
        return max(self.grid_w, 0.0)

    @property
    def grid_export_w(self) -> float:
        return max(-self.grid_w, 0.0)

    @property
    def local_generation_w(self) -> float:
        return max(self.pv_w, 0.0)

    @property
    def self_sufficiency_percent(self) -> float:
        if self.house_w <= 0:
            return 100.0
        return max(
            0.0,
            min(100.0, 100.0 * (1.0 - self.grid_import_w / self.house_w)),
        )

    @property
    def balance_error_w(self) -> float:
        """Diagnostic mismatch between measured supply and demand."""
        supply = self.pv_w + self.grid_import_w + max(-self.battery_w, 0.0)
        demand = (
            self.house_w
            + self.grid_export_w
            + max(self.battery_w, 0.0)
        )
        return supply - demand


@dataclass(frozen=True, slots=True)
class EVState:
    soc_percent: float | None
    connected: bool | None
    charging_power_w: float = 0.0
    target_soc_percent: float = 80.0
    range_km: float | None = None
    departure_at: datetime | None = None
    availability: Availability = Availability.UNKNOWN

    def __post_init__(self) -> None:
        for name, value in {
            "soc_percent": self.soc_percent,
            "target_soc_percent": self.target_soc_percent,
        }.items():
            if value is not None and not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class ChargerState:
    connected: bool | None
    charging: bool
    power_w: float
    current_a: float | None = None
    maximum_current_a: float | None = None
    phases: int | None = None
    availability: Availability = Availability.UNKNOWN


@dataclass(frozen=True, slots=True)
class ClimateState:
    indoor_temperature_c: float | None = None
    target_temperature_c: float | None = None
    hot_water_temperature_c: float | None = None
    power_w: float = 0.0
    mode: OperatingMode = OperatingMode.UNKNOWN
    availability: Availability = Availability.UNKNOWN


@dataclass(frozen=True, slots=True)
class PriceState:
    current_eur_kwh: float | None = None
    next_hour_eur_kwh: float | None = None
    cheapest_next_6h_eur_kwh: float | None = None
    source: str = "unknown"


@dataclass(frozen=True, slots=True)
class ForecastState:
    pv_15m_w: float | None = None
    pv_60m_w: float | None = None
    pv_today_remaining_kwh: float | None = None
    cloud_risk_percent: float | None = None

    def __post_init__(self) -> None:
        if (
            self.cloud_risk_percent is not None
            and not 0.0 <= self.cloud_risk_percent <= 100.0
        ):
            raise ValueError("cloud_risk_percent must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class DeviceHealth:
    states: Mapping[str, Availability] = field(default_factory=dict)

    @property
    def overall(self) -> Availability:
        values = set(self.states.values())
        if Availability.OFFLINE in values:
            return Availability.OFFLINE
        if Availability.DEGRADED in values:
            return Availability.DEGRADED
        if values and values == {Availability.ONLINE}:
            return Availability.ONLINE
        return Availability.UNKNOWN


@dataclass(frozen=True, slots=True)
class DigitalTwin:
    """Complete immutable HEOS snapshot."""

    power: PowerFlow
    ev: EVState
    charger: ChargerState
    climate: ClimateState = field(default_factory=ClimateState)
    price: PriceState = field(default_factory=PriceState)
    forecast: ForecastState = field(default_factory=ForecastState)
    health: DeviceHealth = field(default_factory=DeviceHealth)
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def age_seconds(self) -> float:
        return max(0.0, (datetime.now(UTC) - self.captured_at).total_seconds())

    @property
    def usable_for_autopilot(self) -> bool:
        """Conservative readiness gate for future automatic execution."""
        return (
            self.health.overall in {Availability.ONLINE, Availability.UNKNOWN}
            and self.power.quality.confidence >= 0.80
            and self.power.quality.age_seconds <= 60
            and self.ev.soc_percent is not None
            and self.charger.availability != Availability.OFFLINE
        )

    def summary(self) -> dict[str, float | str | bool | None]:
        """Return a stable diagnostic summary."""
        return {
            "pv_w": self.power.pv_w,
            "house_w": self.power.house_w,
            "grid_import_w": self.power.grid_import_w,
            "grid_export_w": self.power.grid_export_w,
            "self_sufficiency_percent": round(
                self.power.self_sufficiency_percent, 2
            ),
            "ev_soc_percent": self.ev.soc_percent,
            "charger_power_w": self.charger.power_w,
            "health": self.health.overall.value,
            "usable_for_autopilot": self.usable_for_autopilot,
        }
