# RFC-0015 — Operational Release Gate

Status: Accepted  
Milestone: M20  
Package: `heos.release_gate`

## 1. Purpose

M20 closes the operational loop without allowing Strategy or AI components to command
devices. It decides whether a Strategy Decision is sufficiently fresh, explainable,
version-compatible, feasible, safe, and operationally ready to be handed to the
deterministic Decision Compiler.

## 2. Position in the architecture

```text
Forecast (M14)
  -> Feedback (M15)
  -> House Memory (M16)
  -> Digital Twin (M17)
  -> Calibration (M18)
  -> Strategy (M19)
  -> Operational Release Gate (M20)
  -> Decision Compiler
  -> Safety Engine
  -> Arbitration
  -> Executor
```

The gate emits an `ExecutionIntent`. It does not execute Home Assistant services and does
not bypass existing compiler, safety, arbitration, or execution boundaries.

## 3. Inputs

`OperationalRequest` contains:

- a structurally compatible M19 `StrategyDecision`;
- requested operation mode;
- timezone-aware evaluation time;
- complete versioned `SystemManifest`;
- component readiness evidence;
- operator approval and autonomy authorization;
- deterministic metadata.

## 4. Modes

- `observe`: no operational authority beyond observation.
- `advise`: may emit a compiler-targeted recommendation.
- `supervised`: requires explicit operator approval by default.
- `autonomous`: requires operator approval and explicit autonomy authorization by default.

The policy defines the maximum permitted mode. Requests above it are rejected.

## 5. Gates

The implementation evaluates:

- required component manifest completeness;
- mode authorization;
- decision contract shape and minimum alternatives;
- decision freshness and future clock skew;
- selected-strategy feasibility;
- objective score threshold;
- simulated violations;
- objective allow-list;
- strategy policy and twin-parameter versions;
- readiness of Forecast, Feedback, Memory, Digital Twin, Calibration, Strategy,
  Compiler, Safety, and Executor;
- operator approval;
- autonomy authorization.

Every gate produces a machine-readable `GateResult` with an explanation.

## 6. Outcomes

- `released`: every gate passed and an `ExecutionIntent` is emitted.
- `held`: structurally valid request blocked by transient or policy conditions.
- `rejected`: hard contract or mode violation.

## 7. Determinism and auditability

Release and intent identifiers are UUIDv5 values generated from canonical JSON. Immutable
records can be serialized deterministically and stored in an append-only repository.

## 8. Safety invariants

1. M20 never commands a device.
2. M20 never overrides the Safety Engine.
3. M20 never changes a Strategy Decision.
4. A non-released result cannot contain an intent.
5. A released intent targets the Decision Compiler.
6. Missing readiness evidence fails closed.

## 9. Acceptance criteria

- Full repository tests pass.
- Ruff passes.
- M20 focused suite contains at least 80 tests.
- Same input produces the same release record.
- Missing component readiness holds release.
- Invalid decision shape or excessive mode is rejected.
- Supervised and autonomous modes require configured approvals.
- The emitted intent is compiler-targeted, not device-targeted.
