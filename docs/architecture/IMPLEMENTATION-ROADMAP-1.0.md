# HEOS Architecture 1.0 — Implementation Roadmap

## Phase A — Consolidation
- move canonical models into `domain/`
- remove duplicate Event Bus and Decision implementations
- establish public package exports
- enforce dependency rules in tests

## Phase B — Simulation
- add `Scenario`
- add `SimulationResult`
- add deterministic 15-minute simulator
- add cost, comfort and grid scoring

## Phase C — House Memory
- add event history repository
- add outcome evaluation
- add forecast-error tracking
- add confidence adaptation

## Phase D — Capability Registry
- replace device-oriented logic with capabilities
- add capability discovery
- add adapter contract tests
- map Wattpilot, Fronius and Daikin capabilities

## Phase E — Multi-Brain Coordination
- add Brain plugin metadata
- add candidate aggregation
- add conflict resolution
- add whole-home strategy selection

## Phase F — Safe Autopilot
- add command expiry
- add idempotency
- add rollback
- add manual override
- add safety audit log
