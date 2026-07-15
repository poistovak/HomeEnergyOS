# Milestone 21 — Proof-Carrying Decisions

## Added

- self-contained `CertifiedDecision` artifacts for released M20 decisions;
- canonical SHA-256 binding of action, input state, component manifest, model versions, policies and rejected alternatives;
- machine-verifiable evidence claims for release status, gates, compiler target, validity window and source identity;
- tamper-evident certificate chaining and full-chain audit;
- deterministic replay envelopes for incident analysis and counterfactual review;
- append-only proof repository, JSON serialization and orchestration engine;
- 90 focused tests covering determinism, tampering, expiry, serialization, replay and chain integrity.

## Safety boundary

M21 never commands a device. It certifies an already released M20 execution intent and verifies that the intent still carries valid evidence before the deterministic compiler consumes it.
