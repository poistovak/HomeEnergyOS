# RFC-0004 — HEOS Digital Twin

**Status:** Draft  
**Milestone:** Neuron

## Purpose

The Digital Twin is the single normalized representation of the home energy
system. It removes vendor names, Home Assistant entity IDs and transport
details from every brain.

## Snapshot domains

- power flow,
- EV,
- charger,
- climate and hot water,
- electricity price,
- solar forecast,
- device health,
- source quality and freshness.

## Safety

The twin exposes `usable_for_autopilot`, a conservative readiness gate.
Automatic execution must remain disabled when critical data is stale,
low-confidence or unavailable.

## Immutability

Every snapshot is immutable. A changed sensor value creates a new twin instead
of mutating the previous one. This enables deterministic decisions, replay,
testing and the future Decision Timeline.
