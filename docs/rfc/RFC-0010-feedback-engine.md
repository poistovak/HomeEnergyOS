# RFC-0010 — Feedback Engine

## Status
Accepted for Milestone 15.

## Purpose
Milestone 15 closes the deterministic learning loop without allowing learning code to
modify execution. It records a committed decision, records the observed outcome after
the effective window, compares prediction with reality, and materializes an immutable
`ExperienceCandidate` for Milestone 16.

## Pipeline

```text
Decision committed
    -> DecisionRecord
Observed effective window
    -> OutcomeRecord
Pure deterministic comparison
    -> ComparisonRecord
Machine-readable handoff
    -> ExperienceCandidate
```

## Architectural rules

1. Feedback is observational. It never changes the active Execution Plan.
2. Records are immutable and repositories are append-only.
3. Comparison is deterministic for identical decision/outcome inputs.
4. The engine consumes public records only. It does not import Arbitration or Safety internals.
5. Version provenance is mandatory: schema, forecast, model, policy, and compiler.
6. Safety and deterministic execution remain authoritative.

## Metrics

- `prediction_error`
- `execution_error`
- `timing_error`
- `constraint_error`
- `energy_error`
- `overall_score`

All metrics are normalized to `0..1`. Error metrics use `0` as best. `overall_score`
uses `1` as best.

## M16 handoff

`ExperienceCandidate` contains immutable features, targets, quality score,
classification, explanation, and the exact version stamp that produced the decision.
M16 may store or aggregate candidates, but must not rewrite M15 history.
