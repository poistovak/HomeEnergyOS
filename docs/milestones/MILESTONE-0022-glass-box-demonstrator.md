# Milestone 22 — Glass Box Demonstrator

Milestone 22 makes the complete HEOS architecture inspectable with one command.

## Acceptance criteria

- `python -m heos.demo` succeeds from a clean repository.
- the same run produces the same certificate and audit digest;
- strategy, release, proof, compiler, safety, dry-run execution, feedback, and memory are visible;
- report, JSON audit, certificate, and SHA-256 files are generated;
- no physical device command is issued;
- full pytest and Ruff checks pass.
