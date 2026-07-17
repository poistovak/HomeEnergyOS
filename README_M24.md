# HEOS M24 — Resilience and Recovery

M24 converts operational faults and degraded inputs into deterministic,
auditable recovery decisions.

## Install into the repository

Copy the contents of this ZIP over the HomeEnergyOS repository root.

PowerShell:

```powershell
Expand-Archive .\HEOS_M24_Resilience_Recovery.zip -DestinationPath .\M24
Copy-Item .\M24\* .\HomeEnergyOS -Recurse -Force
cd .\HomeEnergyOS
python -m pytest
```

## Boundaries

The resilience layer does not operate devices. It emits a recovery decision
that must still pass through the existing compiler, safety, arbitration, and
execution boundaries.
