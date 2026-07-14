from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class KernelHealth(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class EnergyBalance:
    production_w: float
    consumption_w: float
    storage_charge_w: float
    storage_discharge_w: float
    grid_import_w: float
    grid_export_w: float

    @property
    def net_w(self) -> float:
        return (
            self.production_w
            + self.storage_discharge_w
            + self.grid_import_w
            - self.consumption_w
            - self.storage_charge_w
            - self.grid_export_w
        )

    @property
    def balanced(self) -> bool:
        return abs(self.net_w) < 1.0


@dataclass(frozen=True, slots=True)
class TopologyIssue:
    code: str
    message: str
    resource_id: str | None = None


@dataclass(frozen=True, slots=True)
class KernelSnapshot:
    health: KernelHealth
    balance: EnergyBalance
    resource_count: int
    flow_count: int
    issues: tuple[TopologyIssue, ...] = ()
    created_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
