# Milestone 13 — Decision Arbitration Engine

## Goal

Select one explainable and reproducible winner from multiple future
scenarios.

## Pipeline

```text
Future Scenarios
      ↓
Arbitration Candidates
      ↓
Decision Arbitrator
      ↓
Arbitration Report
      ↓
Selected Future Scenario
```

## Completion criteria

- invalid candidates never win,
- policy priority is explicit,
- ranking is deterministic,
- complete ties use stable scenario ID ordering,
- every result includes a trace,
- no candidates and no valid candidates are handled safely,
- tests and Ruff pass.
