# RFC-0009 — Forecast Core 1.0

**Status:** Proposed  
**Layer:** 5 — Intelligence  
**Milestone:** 14

## Purpose

Forecast Core provides a vendor-neutral and provider-neutral model of the
home's expected future state.

## Core types

- `ForecastPoint`
- `ForecastSeries`
- `ForecastSnapshot`
- `ForecastReport`
- `ForecastProvider`
- `ForecastEngine`

## Rules

- timestamps are timezone-aware,
- series are sorted and contain unique timestamps,
- interpolation is deterministic,
- confidence is explicit,
- missing forecast kinds are reported, not guessed,
- providers are adapters, not part of the core model,
- Forecast Core has no internet dependency.

## Architectural placement

Forecast Core is a subsystem of the Intelligence layer.

It does not create an eighth HEOS layer.
