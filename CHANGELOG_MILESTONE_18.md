# Changelog — Milestone 18

## Calibration Engine

- Added immutable calibration samples, parameter bounds, metric policies, estimates, and reports.
- Added deterministic bounded coordinate search over explicit Digital Twin parameters.
- Added weighted error metrics for temperature, storage state, grid energy, and battery throughput.
- Added optional validation-set acceptance so calibration cannot silently overfit training data.
- Added advisory-only parameter recommendations; M18 never activates parameters or commands devices.
- Added append-only in-memory and JSONL calibration report repositories.
- Added deterministic JSON serialization and stable report identifiers.
- Added 50 focused M18 tests, RFC, milestone documentation, and example.
