# RFC-0005 — HouseState Model

**Status:** Draft  
**Milestone:** Neuron

`HouseState` is the complete immutable context for HEOS decisions.

It combines:

- the current `DigitalTwin`,
- owner intent,
- hard safety constraints,
- predictions,
- operating policy.

```text
HouseState
├── DigitalTwin
├── UserIntent
├── SafetyConstraints
├── PredictionWindow
└── OperatingPolicy
```

The Digital Twin describes reality.  
HouseState describes reality plus what the owner wants and what HEOS is allowed to do.

Brains must receive HouseState and must never read Home Assistant entities directly.
