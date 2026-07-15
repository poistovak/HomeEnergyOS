# HomeEnergyOS Core 0.1.0 — M20 Architecture Release

This release completes the deterministic M14–M20 architecture:

1. Forecast Core
2. Feedback Engine
3. House Memory
4. Digital Twin
5. Calibration Engine
6. Strategy Engine
7. Operational Release Gate

The final gate does not give AI direct control of a home. It converts a validated strategy
into an auditable intent addressed to the Decision Compiler, while Safety, arbitration,
and execution remain independent deterministic boundaries.

## Recommended rollout

1. Observe mode
2. Advise mode
3. Supervised mode after commissioning
4. Autonomous mode only with explicit site authorization and proven safety evidence
