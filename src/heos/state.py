"""Backward-compatible normalized house state.

`HouseState` remains available for early brains. New development should prefer
`DigitalTwin` from `heos.twin`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from .twin import ChargerState, DigitalTwin, EVState, PowerFlow


@dataclass(frozen=True, slots=True)
class HouseState:
    pv_power_w: float
    house_power_w: float
    grid_power_w: float
    ev_soc_percent: float | None = None
    ev_connected: bool | None = None
    ev_charging_power_w: float | None = None
    heat_pump_power_w: float | None = None
    electricity_price_eur_kwh: float | None = None
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def grid_import_w(self) -> float:
        return max(self.grid_power_w, 0.0)

    @property
    def grid_export_w(self) -> float:
        return max(-self.grid_power_w, 0.0)

    @property
    def self_sufficiency_percent(self) -> float:
        if self.house_power_w <= 0:
            return 100.0
        return max(
            0.0,
            min(100.0, 100.0 * (1.0 - self.grid_import_w / self.house_power_w)),
        )

    def to_digital_twin(self) -> DigitalTwin:
        """Convert the legacy state into the richer Digital Twin model."""
        charging_power = self.ev_charging_power_w or 0.0
        return DigitalTwin(
            power=PowerFlow(
                pv_w=self.pv_power_w,
                house_w=self.house_power_w,
                grid_w=self.grid_power_w,
                ev_w=charging_power,
                heat_pump_w=self.heat_pump_power_w or 0.0,
            ),
            ev=EVState(
                soc_percent=self.ev_soc_percent,
                connected=self.ev_connected,
                charging_power_w=charging_power,
            ),
            charger=ChargerState(
                connected=self.ev_connected,
                charging=charging_power > 0,
                power_w=charging_power,
            ),
            captured_at=self.captured_at,
        )
