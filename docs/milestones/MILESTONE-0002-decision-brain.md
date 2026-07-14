# Milestone 2 — First Real Decision Brain

**Status:** Implemented  
**Version:** 0.6.0

## Mission

Prove the HEOS principle:

> Automation executes rules. HEOS makes decisions.

## Contract

```text
Immutable HouseState
        ↓
HomeEnergyBrain
        ↓
Explainable EnergyDecision
```

The brain is:

- deterministic,
- side-effect free,
- vendor independent,
- explainable,
- safety aware,
- testable without hardware.

## Initial decisions

- charge the EV from stable solar surplus,
- stop EV charging when grid import is detected,
- stop at the configured target SOC,
- hold when data quality is insufficient,
- use available solar energy before high cloud risk.

## Explicit exclusions

This milestone does not call:

- Home Assistant services,
- Fronius APIs,
- Wattpilot APIs,
- MQTT,
- cloud services.

Execution remains a separate responsibility of the Safety Layer and
Device Abstraction Layer.
