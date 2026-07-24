# RFC-0012 — Digital Twin

## Status
Accepted for Milestone 17.

## Purpose
The Digital Twin predicts the physical and electrical consequences of a proposed control plan.
It is physics-first, deterministic, explainable, and unable to command devices.

## Contract

1. Inputs are an immutable initial state, parameter set, controls, disturbances, and step duration.
2. Building temperature follows an explicit first-order heat balance.
3. HVAC electric demand follows thermal demand divided by COP.
4. Battery and EV states follow capacity, efficiency, power, and state-of-charge limits.
5. Grid power is an auditable balance of load, HVAC, EV, battery, PV, and curtailment.
6. Every clipped request or hard-limit breach is returned as a machine-readable violation.
7. Repeating the same simulation inputs produces the same trace identifier and state trajectory.
8. M16 patterns may provide bounded residual corrections; physical equations remain authoritative.
9. Simulation traces are immutable and JSON serializable.
10. M17 has no authority to select strategies, bypass Safety, or execute commands.

## Correction boundary
Residual correction is optional. The correction contract is limited to:

- indoor-temperature residual,
- base-load residual,
- PV residual.

Each correction carries its source and explanation. The M16 adapter uses explicit target keys and
bounded corrections. A black-box model cannot replace storage limits, grid limits, or the physical
heat balance.

## Non-goals

- parameter fitting or calibration (M18),
- strategy optimization (M19),
- command generation or execution,
- hidden mutation of House Memory,
- automatic relaxation of hard constraints.

## M18 handoff
M18 Calibration may compare M17 traces with M15 outcomes and M16 memories to propose versioned
parameter updates. It must not rewrite historical traces.
