# HEOS M27 — Outcome Verifier

M27 closes the execution loop. It compares M26 execution evidence with an explicit expected outcome, classifies the result as verified, degraded, failed or inconclusive, recommends bounded retries and records a tamper-evident certificate chain.

## Install

```powershell
Expand-Archive .\HEOS_M27_Outcome_Verifier.zip -DestinationPath .\M27 -Force
Copy-Item .\M27\* .\HomeEnergyOS -Recurse -Force
cd .\HomeEnergyOS
python -m pytest
ruff check .
```
