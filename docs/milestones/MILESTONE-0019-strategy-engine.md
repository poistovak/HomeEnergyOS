# MILESTONE-0019 — Strategy Engine

## Goal

Select the best explainable future operating strategy from explicit candidate schedules
using the calibrated physics-first Digital Twin.

## Acceptance criteria

- [x] Immutable public contracts.
- [x] Deterministic Digital Twin evaluation.
- [x] Configurable multi-objective scoring.
- [x] Feasibility-first ranking.
- [x] Stable tie-breaking and deterministic decision IDs.
- [x] Calibration handoff without parameter activation.
- [x] Standard candidate factory.
- [x] Complete decision serialization.
- [x] Advisory-only safety boundary.
- [x] Focused tests and Ruff validation.

## Handoff to M20

M20 may integrate the selected strategy with the existing compiler, safety,
arbitration, and execution pipeline. M20 must preserve the advisory boundary until the
existing deterministic safety gates accept the plan.
