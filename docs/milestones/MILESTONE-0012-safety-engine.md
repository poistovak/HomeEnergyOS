# Milestone 12 — Safety Engine

## Goal

Allow, defer or deny a compiled plan before execution.

## Pipeline

```text
ExecutionPlan
      ↓
SafetyEngine
      ├── ALLOW
      ├── RETRY_LATER
      └── DENY
```

## Completion criteria

- immutable safety context,
- deterministic rule aggregation,
- explicit findings and reasons,
- deny-over-retry precedence,
- no side effects,
- automated tests,
- Ruff clean.
