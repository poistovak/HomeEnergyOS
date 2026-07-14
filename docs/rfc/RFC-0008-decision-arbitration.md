# RFC-0008 — Decision Arbitration Engine 1.0

**Status:** Proposed  
**Era:** II — Execution  
**Milestone:** 13

## Purpose

The Decision Arbitration Engine selects exactly one valid future scenario
from a set of candidates.

## Ranking order

1. validity,
2. policy priority,
3. scenario score,
4. confidence,
5. scenario ID as a deterministic tie-breaker.

## Principle

The same candidates must produce the same winner regardless of input order.

## Explainability

Every arbitration produces:

- ordered candidate ranking,
- selection reason,
- rejection reason for invalid candidates,
- decision trace,
- selected winner or an explicit no-winner result.

## Boundary

Arbitration does not compile, validate safety, or execute a scenario.
It only selects the winner.
