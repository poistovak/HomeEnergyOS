"""Immutable forecast-domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ForecastValueKind(StrEnum):
    PV_POWER_W = "pv_power_w"
    HOUSE_LOAD_W = "house_load_w"
    GRID_PRICE_EUR_KWH = "grid_price_eur_kwh"
    OUTDOOR_TEMPERATURE_C = "outdoor_temperature_c"
    EV_AVAILABILITY = "ev_availability"
    BATTERY_SOC_PERCENT = "battery_soc_percent"


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    timestamp: datetime
    value: float
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("forecast timestamp must be timezone-aware")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class ForecastSeries:
    series_id: str
    kind: ForecastValueKind
    points: tuple[ForecastPoint, ...]
    source: str
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    def __post_init__(self) -> None:
        if not self.series_id.strip():
            raise ValueError("series_id must not be empty")
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.points:
            raise ValueError("forecast series must contain points")

        timestamps = tuple(point.timestamp for point in self.points)
        if timestamps != tuple(sorted(timestamps)):
            raise ValueError(
                "forecast points must be sorted by timestamp"
            )
        if len(set(timestamps)) != len(timestamps):
            raise ValueError(
                "forecast points must have unique timestamps"
            )

    @property
    def start(self) -> datetime:
        return self.points[0].timestamp

    @property
    def end(self) -> datetime:
        return self.points[-1].timestamp

    def value_at(self, timestamp: datetime) -> ForecastPoint:
        if timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        for point in self.points:
            if point.timestamp == timestamp:
                return point

        if timestamp < self.start or timestamp > self.end:
            raise KeyError(
                f"timestamp outside forecast range: {timestamp.isoformat()}"
            )

        before = self.points[0]
        for after in self.points[1:]:
            if before.timestamp < timestamp < after.timestamp:
                span = (
                    after.timestamp - before.timestamp
                ).total_seconds()
                offset = (
                    timestamp - before.timestamp
                ).total_seconds()
                ratio = offset / span

                return ForecastPoint(
                    timestamp=timestamp,
                    value=before.value + (
                        after.value - before.value
                    ) * ratio,
                    confidence=min(
                        before.confidence,
                        after.confidence,
                    ),
                )
            before = after

        raise KeyError(timestamp)


@dataclass(frozen=True, slots=True)
class ForecastSnapshot:
    timestamp: datetime
    values: tuple[
        tuple[ForecastValueKind, ForecastPoint],
        ...
    ]

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("snapshot timestamp must be timezone-aware")

        kinds = tuple(kind for kind, _ in self.values)
        if len(set(kinds)) != len(kinds):
            raise ValueError(
                "snapshot cannot contain duplicate forecast kinds"
            )

        if any(
            point.timestamp != self.timestamp
            for _, point in self.values
        ):
            raise ValueError(
                "all snapshot points must share snapshot timestamp"
            )

    def get(
        self,
        kind: ForecastValueKind,
    ) -> ForecastPoint | None:
        for item_kind, point in self.values:
            if item_kind is kind:
                return point
        return None


@dataclass(frozen=True, slots=True)
class ForecastReport:
    series: tuple[ForecastSeries, ...]
    snapshots: tuple[ForecastSnapshot, ...]
    missing_kinds: tuple[ForecastValueKind, ...]
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    @property
    def complete(self) -> bool:
        return not self.missing_kinds
