# Milestone 3 — Intelligence Layer

**Status:** Implemented  
**Version:** 0.7.0

## Mission

Transform immutable HouseState snapshots into trusted short-horizon
intelligence before the Decision Brain acts.

```text
HouseState + recent history
          ↓
    Feature Extractor
          ↓
     Trend Estimator
          ↓
    Forecast Engine
          ↓
   Confidence Scorer
          ↓
  IntelligenceResult
```

## Capabilities

- vendor-neutral feature extraction,
- rising, falling and stable trend detection,
- 15-minute PV and household-demand forecast,
- cloud-risk attenuation,
- projected surplus and grid-import risk,
- confidence and freshness scoring,
- explicit decision-readiness gate.

## Design rules

The Intelligence Layer:

- is deterministic,
- has no hardware side effects,
- requires no cloud connection,
- uses no LLM for safety-critical calculations,
- remains testable with synthetic HouseState snapshots.

Machine-learning models may later implement the same public contracts,
but deterministic fallbacks must always remain available.
