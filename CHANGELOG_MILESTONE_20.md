# Milestone 20 — Operational Release Gate

Milestone 20 closes the M14–M20 learning and control architecture with a deterministic
operational release gate.

## Added

- `heos.release_gate` immutable operational-release contracts.
- Versioned system manifest covering Forecast, Feedback, House Memory, Digital Twin,
  Calibration, Strategy, Compiler, Safety, and Execution.
- Explicit operating modes: observe, advise, supervised, and autonomous.
- Deterministic release evaluation with explainable gate results.
- Freshness, feasibility, score, violation, objective, version, readiness, operator,
  and autonomy-authorization gates.
- Compiler-targeted `ExecutionIntent`; the release gate never commands devices directly.
- Append-only in-memory release ledger and deterministic JSON serialization.
- 83 focused tests.

## Safety invariant

A released intent is only an input to the deterministic Decision Compiler. Existing Safety
Engine, arbitration, and executor boundaries remain authoritative.
