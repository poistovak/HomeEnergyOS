from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

class EnergyCarrier(StrEnum):
    ELECTRICITY_AC = "electricity_ac"
    ELECTRICITY_DC = "electricity_dc"
    THERMAL = "thermal"
    FUEL = "fuel"
    MOBILITY = "mobility"

@dataclass(frozen=True, slots=True)
class EnergyFlow:
    source_id: str
    destination_id: str
    carrier: EnergyCarrier
    power_w: float
    efficiency: float = 1.0
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.source_id == self.destination_id:
            raise ValueError("source_id and destination_id must differ")
        if self.power_w < 0:
            raise ValueError("power_w cannot be negative")
        if not 0.0 < self.efficiency <= 1.0:
            raise ValueError("efficiency must be greater than 0 and at most 1")

    @property
    def delivered_power_w(self) -> float:
        return self.power_w * self.efficiency

    @property
    def losses_w(self) -> float:
        return self.power_w - self.delivered_power_w
