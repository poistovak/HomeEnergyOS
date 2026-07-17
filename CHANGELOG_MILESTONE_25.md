# Milestone 25 — Continuity Governor

## Added

- deterministic continuity plans derived from recovery decisions
- bounded retry budgets
- cooldown and deadline enforcement
- explicit approval gates for risky recovery actions
- idempotent plan identifiers
- tamper-evident continuity certificates
- append-only continuity ledger
- focused unit and integration tests

## Safety boundary

M25 never operates a device directly. It produces a bounded continuity plan
that must still pass through HEOS safety, arbitration, and execution layers.
