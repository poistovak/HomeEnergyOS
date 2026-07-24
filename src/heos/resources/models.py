from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ResourceKind(StrEnum):
    PRODUCER = "producer"
    CONSUMER = "consumer"
    STORAGE = "storage"
    CONVERTER = "converter"
    CONTROLLER = "controller"
    GRID = "grid"
    MARKET = "market"
    SENSOR = "sensor"
    FORECAST = "forecast"

class ResourceHealth(StrEnum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass(frozen=True, slots=True)
class ResourceState:
    resource_id: str
    health: ResourceHealth = ResourceHealth.UNKNOWN
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    confidence: float = 1.0
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
