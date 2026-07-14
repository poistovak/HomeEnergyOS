# Capability Layer

## Purpose

The Capability Layer decouples the HEOS intelligence from hardware vendors.

Brains must never depend on:

- Fronius
- BYD
- Daikin
- Wattpilot
- Shelly
- Home Assistant

Brains depend only on Capabilities.

## Golden Rule

Brains know capabilities.

Adapters know devices.

## First Capability

Capability

↓

Adapter

↓

Device

## Capability Layer

HEOS communicates with abstract capabilities instead of vendor-specific APIs.

This allows replacing hardware without changing the decision logic.