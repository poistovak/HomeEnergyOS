# MILESTONE-0018 — Calibration

## Goal

Turn measured house behaviour into a deterministic, explainable Digital Twin parameter candidate.

## Delivered

- immutable calibration contracts;
- bounded calibration of thermal, HVAC, battery, and EV model parameters;
- weighted and normalized model-error metrics;
- optional train/validation separation;
- explicit acceptance thresholds;
- stable calibration report IDs and parameter versions;
- append-only in-memory and JSONL report storage;
- deterministic serialization;
- example and 50 focused tests.

## Acceptance gate

- M17 public `heos.digital_twin` contract is the only Digital Twin dependency;
- no imports from Safety, Arbitration, Strategy, or Execution internals;
- calibration cannot activate parameters or command devices;
- repeated inputs are deterministic;
- all M18 tests pass;
- the complete repository test suite passes after installation;
- Ruff passes;
- Git working tree is reviewed before commit.
