# RFC-0005 — Energy Kernel 1.0

**Status:** Proposed  
**Milestone:** 8

## Purpose

The Energy Kernel is the central nervous system of HEOS.

It coordinates:

- resource registration,
- state observation,
- topology validation,
- energy balance,
- route queries,
- kernel health.

## Boundary

The Kernel knows only:

- `EnergyResource`,
- `ResourceState`,
- `ResourceGraph`,
- `EnergyFlow`,
- resource health and kinds.

The Kernel never imports:

- Fronius,
- Wattpilot,
- Daikin,
- Home Assistant,
- MQTT,
- REST,
- vendor protocols.

## Safety

A failed resource blocks the kernel.

Missing or degraded observations place the kernel into degraded mode.

No execution is part of Milestone 8.
