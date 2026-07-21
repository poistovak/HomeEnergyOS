from datetime import UTC, datetime

import pytest

from heos.forecast import (
    ForecastPoint,
    ForecastSeries,
    ForecastValueKind,
)


def make_series():
    now = datetime.now(UTC)

    return ForecastSeries(
        series_id="pv-001",
        kind=ForecastValueKind.PV_POWER_W,
        source="static",
        points=(
            ForecastPoint(
                timestamp=now,
                value=6200.0,
                confidence=0.95,
            ),
        ),
    )


def test_forecast_series_is_ready_for_verification():
    series = make_series()

    assert series.kind == ForecastValueKind.PV_POWER_W
    assert series.points[0].value == 6200.0


def test_forecast_rejects_empty_series():
    with pytest.raises(ValueError):
        ForecastSeries(
            series_id="pv",
            kind=ForecastValueKind.PV_POWER_W,
            source="test",
            points=(),
        )


def test_forecast_point_requires_timezone():
    with pytest.raises(ValueError):
        ForecastPoint(
            timestamp=datetime.now(),
            value=10.0,
        )


def test_forecast_confidence_contract():
    with pytest.raises(ValueError):
        ForecastPoint(
            timestamp=datetime.now(UTC),
            value=10.0,
            confidence=2.0,
        )