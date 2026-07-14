# Milestone 6 — Real World, Read Only

## Mission

Connect HEOS to Pavel's real Home Assistant data without allowing any device control.

## Scope

- real Home Assistant entity mapping,
- read-only snapshot collection,
- snapshot health validation,
- human-readable real-home report,
- dry-run by default,
- no service calls,
- no live control.

## First deployment target

- Fronius GEN24
- Fronius Smart Meter
- Wattpilot
- Omoda 9
- Daikin Altherma
- Home Assistant

## Safety gate

Milestone 6 is complete only when real data can be read repeatedly and validated for several days without a single write command.

Live control belongs to a later milestone.
