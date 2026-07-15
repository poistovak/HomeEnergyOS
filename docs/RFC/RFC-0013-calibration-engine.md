# RFC-0013 — Calibration Engine

## Status

Accepted for Milestone 18.

## Purpose

M18 compares Digital Twin predictions with observed state transitions and proposes bounded,
versioned parameter candidates. It improves the model without granting calibration authority over
Safety, Arbitration, Strategy, or device execution.

## Contract

1. Input is an immutable set of `CalibrationSample` records and an explicit base `TwinParameters`.
2. Only parameters listed in `CalibratableParameter` may be estimated.
3. Every estimated parameter requires explicit lower and upper bounds.
4. Search is deterministic, bounded, and independent of wall-clock time.
5. Error is reported separately for indoor temperature, battery state, EV state, grid import,
   grid export, and battery throughput.
6. Metric weights and normalization scales are explicit and versioned by `CalibrationPolicy`.
7. Validation samples, when supplied, decide acceptance; training loss alone cannot override them.
8. A report is advisory. It never mutates a running Digital Twin or sends commands.
9. Repeated inputs produce the same parameter candidate and report identifier.
10. Reports are immutable, JSON serializable, and append-only when persisted.

## Safety boundary

M18 does not calibrate grid limits, indoor safety limits, maximum device power, or any other hard
constraint. Those values remain configuration and Safety responsibilities.

## M19 handoff

M19 Strategy may compare scenarios using an explicitly accepted M18 parameter version. Rejected
reports keep the original parameters as `recommended_parameters`.
