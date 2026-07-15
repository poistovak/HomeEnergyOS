# MILESTONE-0020 — Operational Release Gate

## Goal

Turn the advisory M19 Strategy Decision into a deterministic, explainable, fail-closed
handoff to the existing Decision Compiler.

## Delivered

- immutable release contracts;
- complete system-version manifest;
- four explicit operating modes;
- deterministic release supervisor;
- readiness, safety, approval, and compatibility gates;
- compiler-targeted execution intent;
- append-only release repository;
- deterministic serialization;
- example and focused test suite.

## Definition of done

```text
M14 Forecast Core                 complete
M15 Feedback Engine              complete
M16 House Memory                 complete
M17 Digital Twin                 complete
M18 Calibration Engine           complete
M19 Strategy Engine              complete
M20 Operational Release Gate     complete
```

M20 is a release boundary, not a device driver. Production deployment still requires
real-device adapters, site configuration, commissioning, and staged validation in
observe/advise mode before higher authority is enabled.
