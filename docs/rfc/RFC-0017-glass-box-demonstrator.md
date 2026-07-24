# RFC-0017: Glass Box Demonstrator

## Status
Accepted for Milestone 22.

## Goal
Provide a deterministic, one-command demonstration of the HomeEnergyOS decision path without cloud services, Home Assistant, or physical devices.

## Command

```bash
python -m heos.demo
```

## Pipeline

1. Build a fixed house state and forecast horizon.
2. evaluate competing strategies with the calibrated Digital Twin contract.
3. admit the selected strategy through the Operational Release Gate.
4. attach and verify a Proof-Carrying Decision certificate.
5. compile the admitted intent into deterministic execution steps.
6. evaluate the plan with the Safety Engine.
7. execute only through the dry-run driver.
8. compare predicted and observed outcomes through Feedback Engine.
9. store the resulting experience in House Memory.
10. write a human report, machine audit, certificate, and SHA-256 digest.

## Safety boundary
The demonstrator never sends a command to a physical device. It does not bypass the Safety Engine and it uses advisory release mode.

## Determinism
The scenario, timestamps, inputs, versions, IDs, certificate, replay token, audit document, and audit digest are deterministic. Runtime-only timestamps are deliberately excluded from the audit payload.
