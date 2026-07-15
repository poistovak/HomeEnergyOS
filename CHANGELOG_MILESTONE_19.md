# Milestone 19 — Strategy Engine

## Added

- Immutable strategy request, candidate, policy, metrics, evaluation, and decision contracts.
- Deterministic candidate simulation through the M17 Digital Twin.
- Multi-objective scoring for energy cost, peak import, battery throughput, comfort,
  EV target, battery reserve, and constraint violations.
- Feasibility-first deterministic ranking with stable tie-breaking.
- Standard bounded candidate factory for balanced, self-consumption, comfort,
  reserve, EV-priority, and idle strategies.
- Optional use of accepted M18 calibrated parameters.
- JSON round-trip serialization for complete strategy decisions.
- 70 focused tests.

## Safety boundary

The Strategy Engine is advisory. It evaluates and ranks candidate schedules but does not
activate parameters, bypass safety, compile execution plans, or command devices.
