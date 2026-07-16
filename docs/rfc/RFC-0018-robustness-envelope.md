# RFC-0018 — Robustness Envelope

## Status

Accepted for Milestone 23.

## Problem

A deterministic strategy may be safe and optimal for one exact forecast while becoming fragile
when photovoltaic production, base load, outdoor temperature, or tariffs deviate from that
forecast. A proof for a single state is not a proof of robustness.

## Decision

HEOS introduces a bounded, deterministic counterfactual grid. The selected baseline strategy is
replayed across every allowed perturbation. For each variant HEOS records feasibility, strategy
selection stability, regret against the best available candidate, peak import, and final energy
state. The complete variant set is hashed into a robustness certificate.

## Architectural constraints

- The component is advisory only.
- It sends no device commands.
- It does not replace the Operational Release Gate, Proof-Carrying Decisions, Safety Engine, or
  Execution Runtime.
- Perturbation generation and ranking are deterministic.
- Every threshold and model version is explicit.
- The certificate is invalid if any variant result is changed.

## Public API

- `RobustnessPolicy`
- `Perturbation`
- `RobustnessEngine`
- `RobustnessRun`
- `verify_run`
- `python -m heos.robustness`

## Acceptance

A clean installation must pass the complete HEOS test suite, Ruff, and the one-command robustness
smoke test. Repeated runs with the same inputs must produce identical certificates.
