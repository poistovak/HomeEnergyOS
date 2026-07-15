# Milestone 17 — Digital Twin

## Added

- immutable digital-twin contracts for state, controls, disturbances, parameters, corrections,
  constraint violations, simulation steps, and traces;
- deterministic physics for building heat balance, HVAC electrical demand, battery storage,
  EV charging, PV curtailment, and grid exchange;
- explicit feasibility reporting for storage, grid, PV, and indoor-temperature constraints;
- physics-first simulation engine with deterministic trace identifiers;
- optional bounded residual correction interface;
- M16 `PatternSummary` residual adapter without granting memory authority over physics;
- deterministic JSON serialization for simulation traces;
- 57 focused M17 tests.

## Architecture

M17 predicts consequences only. It does not select a strategy, modify safety constraints,
or execute device commands.
