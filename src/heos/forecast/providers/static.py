"""Offline deterministic provider for tests and simulations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..models import ForecastSeries, ForecastValueKind


@dataclass(frozen=True, slots=True)
class StaticForecastProvider:
    provider_id: str
    series_by_kind: tuple[
        tuple[ForecastValueKind, ForecastSeries],
        ...
    ]

    @property
    def supported_kinds(self) -> frozenset[ForecastValueKind]:
        return frozenset(
            kind for kind, _ in self.series_by_kind
        )

    def forecast(
        self,
        *,
        kind: ForecastValueKind,
        start: datetime,
        end: datetime,
    ) -> ForecastSeries:
        for item_kind, series in self.series_by_kind:
            if item_kind is not kind:
                continue

            if series.start > start or series.end < end:
                raise ValueError(
                    "static forecast does not cover requested range"
                )
            return series

        raise KeyError(
            f"provider {self.provider_id!r} does not support {kind.value}"
        )
