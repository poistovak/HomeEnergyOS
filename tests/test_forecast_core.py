from datetime import UTC, datetime, timedelta

import pytest

from heos.forecast import (
    ForecastEngine,
    ForecastPoint,
    ForecastSeries,
    ForecastValueKind,
    StaticForecastProvider,
)

START = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
MIDDLE = START + timedelta(minutes=30)
END = START + timedelta(hours=1)


def pv_series() -> ForecastSeries:
    return ForecastSeries(
        series_id="pv.main",
        kind=ForecastValueKind.PV_POWER_W,
        source="static",
        points=(
            ForecastPoint(START, 2000, 0.95),
            ForecastPoint(END, 6000, 0.90),
        ),
    )


def load_series() -> ForecastSeries:
    return ForecastSeries(
        series_id="load.house",
        kind=ForecastValueKind.HOUSE_LOAD_W,
        source="static",
        points=(
            ForecastPoint(START, 1000, 0.90),
            ForecastPoint(END, 2000, 0.85),
        ),
    )


def provider() -> StaticForecastProvider:
    return StaticForecastProvider(
        provider_id="static.home",
        series_by_kind=(
            (ForecastValueKind.PV_POWER_W, pv_series()),
            (
                ForecastValueKind.HOUSE_LOAD_W,
                load_series(),
            ),
        ),
    )


def test_series_interpolates_value() -> None:
    point = pv_series().value_at(MIDDLE)

    assert point.value == 4000
    assert point.confidence == 0.90


def test_series_rejects_naive_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ForecastPoint(
            datetime(2026, 7, 14, 10, 0),  # noqa: DTZ001
            1000,
        )


def test_engine_builds_snapshot_from_multiple_series() -> None:
    report = ForecastEngine((provider(),)).build(
        kinds=(
            ForecastValueKind.PV_POWER_W,
            ForecastValueKind.HOUSE_LOAD_W,
        ),
        start=START,
        end=END,
        snapshot_times=(START, MIDDLE, END),
    )

    middle = report.snapshots[1]
    pv = middle.get(ForecastValueKind.PV_POWER_W)
    load = middle.get(ForecastValueKind.HOUSE_LOAD_W)

    assert pv is not None
    assert load is not None
    assert pv.value == 4000
    assert load.value == 1500
    assert report.complete is True


def test_engine_reports_missing_kind() -> None:
    report = ForecastEngine((provider(),)).build(
        kinds=(
            ForecastValueKind.PV_POWER_W,
            ForecastValueKind.GRID_PRICE_EUR_KWH,
        ),
        start=START,
        end=END,
        snapshot_times=(START,),
    )

    assert report.missing_kinds == (
        ForecastValueKind.GRID_PRICE_EUR_KWH,
    )
    assert report.complete is False


def test_engine_is_deterministic_for_input_order() -> None:
    engine = ForecastEngine((provider(),))

    first = engine.build(
        kinds=(
            ForecastValueKind.PV_POWER_W,
            ForecastValueKind.HOUSE_LOAD_W,
        ),
        start=START,
        end=END,
        snapshot_times=(END, START, MIDDLE),
    )
    second = engine.build(
        kinds=(
            ForecastValueKind.PV_POWER_W,
            ForecastValueKind.HOUSE_LOAD_W,
        ),
        start=START,
        end=END,
        snapshot_times=(MIDDLE, END, START),
    )

    assert first.series == second.series
    assert first.snapshots == second.snapshots
    assert first.missing_kinds == second.missing_kinds


def test_duplicate_provider_ids_are_rejected() -> None:
    duplicate = StaticForecastProvider(
        provider_id="static.home",
        series_by_kind=(
            (ForecastValueKind.PV_POWER_W, pv_series()),
        ),
    )

    with pytest.raises(ValueError, match="must be unique"):
        ForecastEngine((provider(), duplicate))


def test_static_provider_requires_full_range_coverage() -> None:
    short_series = ForecastSeries(
        series_id="pv.short",
        kind=ForecastValueKind.PV_POWER_W,
        source="static",
        points=(
            ForecastPoint(START, 1000),
            ForecastPoint(MIDDLE, 2000),
        ),
    )
    short_provider = StaticForecastProvider(
        provider_id="static.short",
        series_by_kind=(
            (
                ForecastValueKind.PV_POWER_W,
                short_series,
            ),
        ),
    )

    with pytest.raises(ValueError, match="does not cover"):
        short_provider.forecast(
            kind=ForecastValueKind.PV_POWER_W,
            start=START,
            end=END,
        )
