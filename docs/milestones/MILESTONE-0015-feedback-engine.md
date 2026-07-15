# Milestone 15 — Feedback Engine

## Delivered

- immutable decision/outcome/comparison/experience records,
- deterministic comparison and scoring,
- root-cause classification and confidence,
- append-only in-memory repository,
- query filters for scenario, classification, and time,
- runtime-report adapter,
- M16-ready `ExperienceCandidate`,
- 37 automated tests,
- RFC-0010 and executable example.

## Acceptance commands

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check .
```

Expected after merging into the 72-test Milestone 14 baseline: **109 tests**.
