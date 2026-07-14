# Milestone 4 — Home Assistant Bridge

**Status:** Implemented  
**Version:** 0.8.0

## Mission

Connect HEOS to a real home without coupling the Core or Decision Brain
to Home Assistant entity IDs.

```text
Home Assistant entities
          ↓
   EntityMap + Adapter
          ↓
   RawEnergySnapshot
          ↓
    HEOS domain model
          ↓
  Intelligence + Brain
          ↓
   Service Commands
          ↓
    Dry-run Executor
```

## Included

- minimal Home Assistant client port,
- configurable semantic entity map,
- read-only snapshot collection,
- fail-safe numeric validation,
- decision-to-service-command translation,
- dry-run execution by default,
- explicit opt-in live executor,
- automated tests.

## Safety

Milestone 4 does not enable live control automatically.

Live service calls require:

- an explicit live executor,
- `enabled=True`,
- a previously validated decision,
- future integration with the HEOS Safety Layer.

The default execution mode remains dry-run.
