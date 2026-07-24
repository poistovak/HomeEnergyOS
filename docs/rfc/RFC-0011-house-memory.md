# RFC-0011 — House Memory

## Status
Accepted for Milestone 16.

## Purpose
House Memory converts immutable `ExperienceCandidate` records from M15 into durable,
queryable memories. It does not change decisions, safety constraints, or execution.

## Contract

1. Input is the public M15 `ExperienceCandidate` contract.
2. Memory records are immutable and append-only.
3. Retried ingestion is idempotent; conflicting rewrites are rejected.
4. Persistent storage is JSON Lines so each appended record remains independently readable.
5. Recall supports deterministic filters by time, quality, tags, classification, numeric ranges,
   and component versions.
6. Similarity recall uses only supplied numeric features and returns an explainable score,
   overlap, and matched dimensions.
7. Pattern summaries are deterministic aggregates over an explicit set of memory records.
8. M16 has no authority to command devices or bypass Arbitration, Safety, or Execution.

## Non-goals

- model training,
- automatic policy modification,
- deletion or mutation of historical records,
- control-loop execution,
- probabilistic black-box ranking.

## M17 handoff
M17 Digital Twin may consume recalled memories and pattern summaries as evidence. Physical
constraints remain authoritative.
