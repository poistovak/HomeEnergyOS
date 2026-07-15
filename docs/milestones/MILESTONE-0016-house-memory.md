# Milestone 16 — House Memory

## Delivered

- immutable `HouseMemoryRecord`, `MemoryQuery`, `MemoryMatch`, and `PatternSummary`,
- deterministic fingerprints and numeric similarity,
- in-memory and durable append-only JSONL repositories,
- idempotent ingestion from M15 `ExperienceCandidate`,
- deterministic recall, similarity ranking, and pattern summaries,
- serialization round trips,
- comprehensive tests and a PowerShell installer.

## Acceptance gate

```powershell
py -m pytest -q
py -m ruff check .
git status
```

The milestone is accepted only when tests and Ruff pass in the complete repository and the
working tree contains only the intended M16 changes.
