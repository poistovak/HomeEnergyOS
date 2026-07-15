# RFC-0016 — Proof-Carrying Decisions

Status: implemented by Milestone 21

## 1. Problem

An autonomous system must not ask operators to trust a sentence such as “the AI decided this.” A released action must carry enough immutable evidence for another process to verify what was selected, which state and software versions were used, which safety gates passed and whether the action is still valid.

Logs alone are insufficient. They can be incomplete, reordered or detached from the action they describe. M21 therefore turns every M20 release into a self-contained, tamper-evident artifact.

## 2. Principle

> Every autonomous decision must prove that it is the same decision that passed the release gate.

M21 does not prove arbitrary mathematical safety. It provides a deterministic cryptographic proof envelope over evidence already produced by HEOS:

- M19 strategy identity and selected control payload;
- M20 release status, gate results and execution intent;
- the exact input-state snapshot;
- component and model versions;
- release-policy and proof-policy versions;
- rejected alternative snapshots;
- the previous certificate fingerprint when chaining is used.

## 3. Boundary

M21 is downstream of the Operational Release Gate and upstream of the deterministic Decision Compiler.

```text
M19 Strategy Decision
        ↓
M20 Operational Release Gate
        ↓ released ExecutionIntent
M21 Proof-Carrying Decision
        ↓ verified certificate
M10 Decision Compiler
        ↓
M12 Safety Engine
        ↓
M11 Execution Runtime
```

M21 never talks to devices and cannot bypass the compiler, Safety Engine or executor.

## 4. Artifact

`CertifiedDecision` contains:

- a canonical release snapshot;
- a canonical state snapshot;
- component and model version manifests;
- compiler target and numeric control payload;
- canonical rejected-alternative snapshots;
- the proof-policy snapshot;
- a `DecisionCertificate` containing SHA-256 digests and evidence claims.

The certificate identifier is derived from the canonical unsigned certificate body. Changing any bound field changes the identifier or fails verification.

## 5. Evidence claims

The default proof policy requires all of these claims to pass:

1. release status is `released`;
2. an execution intent is present;
3. release and intent share the source-decision identity;
4. all M20 gates passed;
5. the intent targets an allowed deterministic compiler;
6. certificate issue time is inside the intent validity window;
7. the control payload is finite and uniquely keyed;
8. the component manifest is present;
9. required model versions are present and bound to the manifest;
10. the input state is bound;
11. proof and release policies are bound;
12. rejected alternatives are bound;
13. the predecessor link satisfies the chain policy.

Each claim carries its own evidence hash. The verifier recomputes the claims instead of trusting their stored text.

## 6. Canonicalization

Canonical JSON uses sorted keys, compact separators, explicit timezone-aware ISO timestamps and rejects non-finite floating-point values. SHA-256 is the initial hash algorithm.

## 7. Verification

Verification independently recomputes:

- the certificate identifier;
- release, state, manifest, model, policy, action and alternative digests;
- all evidence claims;
- source and intent bindings;
- the execution validity window;
- the predecessor fingerprint.

Any critical mismatch makes the report invalid.

## 8. Chain and replay

Certificates may form an append-only hash chain. `audit_chain()` detects reordered, removed or incorrectly linked certificates.

`replay_envelope()` produces a deterministic token and the exact bound inputs required for an audit replay. Replaying the physical simulation remains the responsibility of Digital Twin and Strategy layers; M21 guarantees that replay receives the same certified evidence.

## 9. Non-goals

- replacing M12 Safety Engine;
- signing with private keys or establishing external identity;
- proving correctness of physical equations;
- commanding a device;
- allowing a language model to approve its own action.

Digital signatures, hardware-backed keys and external transparency logs are possible later extensions.
