# MILESTONE-0017 — Digital Twin

## Goal
Create a deterministic physics-first model of house energy and thermal behaviour.

## Delivered

- thermal envelope and HVAC model,
- battery and EV storage model,
- PV, load, curtailment, and grid balance,
- explicit feasibility violations,
- multi-step simulation traces,
- bounded M16 residual correction adapter,
- deterministic serialization and trace IDs,
- example and tests.

## Acceptance gate

- M16 public `PatternSummary` contract remains the only memory dependency;
- no imports from Safety, Arbitration, or Execution internals;
- repeated inputs are deterministic;
- all M17 tests pass;
- complete repository test suite passes after installation;
- Ruff passes;
- Git working tree is reviewed before commit.
