# RFC-0003 — Brain API

**Status:** Draft  
**Milestone:** Neuron

A brain receives a normalized `HouseState` and returns zero or more immutable
`Decision` objects.

A brain:

- may inspect state,
- may propose and explain,
- must not call Home Assistant services,
- must not directly control a device,
- must not bypass the Safety Layer,
- must be deterministic for identical inputs and policy.

The first built-in implementation is `EVChargingBrain`.
