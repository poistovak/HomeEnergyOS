# RFC-0006 — Execution Runtime 1.0

**Era:** II — Execution  
**Milestone:** 11

The runtime interprets a compiled `ExecutionPlan` through a transport-neutral
`ExecutionDriver`.

Rules:

- deterministic step order,
- stop on first failure,
- every step creates a journal entry,
- empty plans are blocked,
- dry-run is the default,
- no vendor or Home Assistant knowledge in the runtime.
