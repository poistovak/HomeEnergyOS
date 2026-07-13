# RFC-0002 — Decision Engine

**Status:** Draft  
**Milestone:** Neuron

## Goal

Select one explainable decision from multiple brain proposals without allowing
any brain to execute a device action.

## Candidate score

The initial deterministic score combines:

- explicit priority,
- decision confidence,
- bounded utility.

Expired and low-confidence candidates are rejected before ranking.

## Auditability

Every evaluation returns:

- the selected candidate,
- all considered candidates in rank order,
- all rejected candidates.

This audit trail will later feed the HEOS Decision Timeline.
