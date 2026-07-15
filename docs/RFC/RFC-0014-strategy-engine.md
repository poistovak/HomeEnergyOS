# RFC-0014 — Strategy Engine

**Status:** Accepted for Milestone 19  
**Layer:** Advisory planning  
**Depends on:** M17 Digital Twin, M18 Calibration  
**Must not bypass:** Decision Compiler, Safety Engine, Arbitration, Execution Runtime

## 1. Purpose

M19 converts a set of explicit candidate control schedules into a deterministic,
explainable ranking. Each candidate is simulated by the Digital Twin and scored against
one immutable policy.

M19 does not invent device commands at runtime and does not execute anything.

## 2. Inputs

A `StrategyRequest` contains:

- initial Digital Twin state,
- forecast disturbances for every horizon step,
- tariff values,
- comfort bands,
- step duration,
- generation timestamp,
- optional metadata.

A `StrategyCandidate` contains an identifier, objective, tags, and one `TwinControl`
for each horizon step.

## 3. Evaluation

Every candidate is evaluated with the same:

- Digital Twin parameters,
- residual correction model, when configured,
- tariff horizon,
- comfort horizon,
- strategy policy.

The score includes configurable components for:

- net energy cost,
- peak grid import,
- battery throughput,
- comfort deviation,
- EV state-of-charge shortfall,
- battery reserve shortfall,
- constraint count and magnitude.

## 4. Ranking

When `require_feasible` is enabled, feasible candidates are always ranked before
infeasible candidates. Remaining ordering is deterministic:

1. objective score,
2. objective name,
3. candidate identifier.

If no candidate is feasible, selection fails with `NoFeasibleStrategyError`.

## 5. Calibration handoff

`parameters_from_calibration()` accepts the `recommended_parameters` property from an
M18 calibration report. Rejected calibration reports therefore naturally return their
base parameters.

M19 never activates a calibration report itself.

## 6. Standard candidate factory

`StandardStrategyFactory` creates bounded baseline candidates. It is intentionally
simple and deterministic. External planners may supply richer candidates as long as
they satisfy the same immutable contract.

## 7. Output

`StrategyDecision` contains:

- deterministic decision identifier,
- selected rank-one evaluation,
- all ranked alternatives,
- policy and parameter versions,
- explanation.

The complete decision can be serialized to canonical JSON.

## 8. Safety boundary

M19:

- does not command devices,
- does not write to Home Assistant,
- does not bypass the compiler or safety layers,
- does not mutate Digital Twin parameters,
- does not learn online.

Its output is advisory input for the M20 integration and release layer.
