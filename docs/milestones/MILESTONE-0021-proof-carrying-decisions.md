# Milestone 21 — Proof-Carrying Decisions

## Goal

Convert a released M20 execution intent into a deterministic, self-verifying and tamper-evident decision artifact.

## Delivered

- `heos.proof_carrying.ProofBuilder`;
- `heos.proof_carrying.ProofVerifier`;
- `ProofCarryingDecisionEngine`;
- immutable evidence claims and certificates;
- canonical serialization and SHA-256 integrity;
- append-only repository;
- certificate-chain audit;
- deterministic replay envelope;
- RFC, example and focused test suite.

## Acceptance criteria

- a valid M20 released decision can be certified;
- held or rejected decisions cannot be certified;
- failed gates, invalid compiler targets, non-finite controls, missing model versions and invalid time windows are refused;
- state, action, manifest, policy, model, alternative, claim and chain tampering are detected;
- serialization round-trips without changing the certificate;
- focused tests pass;
- full HEOS test suite passes after installation;
- Ruff passes;
- installer artifacts remain outside the repository.

## Operational rule

A downstream compiler should consume only a `CertifiedDecision` whose verification report is valid at execution time.
