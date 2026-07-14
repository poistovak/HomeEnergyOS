"""Forecast-provider contract."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .models import ForecastSeries, ForecastValueKind


class ForecastProvider(Protocol):
    provider_id: str
    supported_kinds: frozenset[ForecastValueKind]

    def forecast(
        self,
        *,
        kind: ForecastValueKind,
        start: datetime,
        end: datetime,
    ) -> ForecastSeries:
        """Return one deterministic forecast series."""
