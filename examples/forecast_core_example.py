from datetime import UTC, datetime, timedelta

from heos.forecast import (
    ForecastEngine,
    ForecastPoint,
    ForecastSeries,
    ForecastValueKind,
    StaticForecastProvider,
)

start = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
end = start + timedelta(hours=1)

pv = ForecastSeries(
    series_id="pv.main",
    kind=ForecastValueKind.PV_POWER_W,
    source="static",
    points=(
        ForecastPoint(start, 2000, 0.95),
        ForecastPoint(end, 6000, 0.90),
    ),
)

provider = StaticForecastProvider(
    provider_id="static.example",
    series_by_kind=(
        (ForecastValueKind.PV_POWER_W, pv),
    ),
)

report = ForecastEngine((provider,)).build(
    kinds=(ForecastValueKind.PV_POWER_W,),
    start=start,
    end=end,
    snapshot_times=(
        start,
        start + timedelta(minutes=30),
        end,
    ),
)

for snapshot in report.snapshots:
    point = snapshot.get(ForecastValueKind.PV_POWER_W)
    print(snapshot.timestamp.isoformat(), point.value if point else None)
