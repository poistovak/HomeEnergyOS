from datetime import UTC, datetime

import pytest

from heos.forecast import (
    ForecastPoint,
    ForecastSeries,
    ForecastValueKind,
)


def make_forecast():
    return ForecastSeries(
        series_id="pv-learning-001",
        kind=ForecastValueKind.PV_POWER_W,
        source="forecast-core",
        points=(
            ForecastPoint(
                timestamp=datetime.now(UTC),
                value=6200.0,
                confidence=0.9,
            ),
        ),
    )


def test_forecast_record_can_be_used_for_learning():
    forecast = make_forecast()

    assert forecast.series_id == "pv-learning-001"
    assert forecast.points[0].value == 6200.0


def test_forecast_learning_requires_confidence():
    with pytest.raises(ValueError):
        ForecastPoint(
            timestamp=datetime.now(UTC),
            value=5000.0,
            confidence=-0.1,
        )


def test_forecast_learning_keeps_metric_identity():
    forecast = make_forecast()

    assert forecast.kind == ForecastValueKind.PV_POWER_W