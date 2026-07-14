# RFC-0007 — Safety Engine 1.0

**Status:** Proposed  
**Era:** II — Execution  
**Milestone:** 12

## Principle

A rejected unsafe action is a successful decision.

## Responsibility

The Safety Engine searches for reasons why a compiled plan must not
execute.

It returns one of:

- `ALLOW`
- `RETRY_LATER`
- `DENY`

## Initial rules

- Kernel health
- Manual execution lock
- Maximum projected grid import
- Verification after every state-changing step

## Determinism

Every rule is side-effect free.

Final severity is deterministic:

```text
DENY > RETRY_LATER > ALLOW
```

## Boundary

The Safety Engine does not execute plans and does not communicate
with devices.
