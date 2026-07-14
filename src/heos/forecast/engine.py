"""Provider-neutral forecast aggregation engine."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from .models import (
    ForecastReport,
    ForecastSeries,
    ForecastSnapshot,
    ForecastValueKind,
)
from .provider import ForecastProvider


class ForecastEngine:
    def __init__(
        self,
        providers: Iterable[ForecastProvider],
    ) -> None:
        self._providers = tuple(providers)

        provider_ids = tuple(
            provider.provider_id
            for provider in self._providers
        )
        if len(set(provider_ids)) != len(provider_ids):
            raise ValueError(
                "forecast provider IDs must be unique"
            )

    def build(
        self,
        *,
        kinds: Iterable[ForecastValueKind],
        start: datetime,
        end: datetime,
        snapshot_times: Iterable[datetime],
    ) -> ForecastReport:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError(
                "forecast range must be timezone-aware"
            )
        if end <= start:
            raise ValueError("forecast end must be after start")

        requested_kinds = tuple(dict.fromkeys(kinds))
        series: list[ForecastSeries] = []
        missing: list[ForecastValueKind] = []

        for kind in requested_kinds:
            provider = self._provider_for(kind)
            if provider is None:
                missing.append(kind)
                continue

            series.append(
                provider.forecast(
                    kind=kind,
                    start=start,
                    end=end,
                )
            )

        ordered_times = tuple(sorted(set(snapshot_times)))
        snapshots = tuple(
            self._snapshot_at(
                timestamp=timestamp,
                series=tuple(series),
            )
            for timestamp in ordered_times
        )

        return ForecastReport(
            series=tuple(series),
            snapshots=snapshots,
            missing_kinds=tuple(missing),
        )

    def _provider_for(
        self,
        kind: ForecastValueKind,
    ) -> ForecastProvider | None:
        for provider in self._providers:
            if kind in provider.supported_kinds:
                return provider
        return None

    @staticmethod
    def _snapshot_at(
        *,
        timestamp: datetime,
        series: tuple[ForecastSeries, ...],
    ) -> ForecastSnapshot:
        values = tuple(
            (
                item.kind,
                item.value_at(timestamp),
            )
            for item in series
            if item.start <= timestamp <= item.end
        )

        return ForecastSnapshot(
            timestamp=timestamp,
            values=values,
        )
