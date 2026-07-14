# Milestone 14 — Forecast Core

## Goal

Give HEOS a provider-neutral representation of energetic time.

## Pipeline

```text
Forecast Providers
      ↓
ForecastSeries
      ↓
ForecastEngine
      ↓
ForecastSnapshot / ForecastReport
      ↓
Future Scenario Planner
```

## Included

- deterministic interpolation,
- explicit confidence,
- multi-series snapshots,
- missing-provider reporting,
- static offline provider,
- automated tests.

## Excluded

- weather API,
- cloud services,
- machine learning,
- planner integration.

Those belong to later milestones.
