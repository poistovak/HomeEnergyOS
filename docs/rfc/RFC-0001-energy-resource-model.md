# RFC-0001 — Energy Resource Model 1.0

**Status:** Proposed  
**Milestone:** 7

HEOS models energy resources, not devices.

Core entities:

- `EnergyResource`
- `ResourceIdentity`
- `ResourceState`
- `EnergyFlow`
- `ResourceRegistry`
- `ResourceGraph`

Resources are nodes. Directed energy flows are edges.

Stable identities are independent of vendor, protocol and Home Assistant entity IDs.

Examples:

```text
producer.solar_roof
converter.house_bus
storage.omoda_9
consumer.daikin
grid.main
```

Adapters translate vendor data into resource states. Brains and decision logic never import vendor adapters.
