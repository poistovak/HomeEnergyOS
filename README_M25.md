# HEOS M25 — Continuity Governor

M25 transforms an M24-style recovery decision into a deterministic,
auditable continuity plan.

The governor answers four questions:

1. Is automatic continuity allowed?
2. Which bounded action is permitted?
3. How many retries are allowed?
4. When must HEOS stop and request approval?

## Install

Copy the ZIP contents over the HomeEnergyOS repository root.

PowerShell:

```powershell
Expand-Archive .\HEOS_M25_Continuity_Governor.zip -DestinationPath .\M25 -Force
Copy-Item .\M25\* .\HomeEnergyOS -Recurse -Force
cd .\HomeEnergyOS
python -m pytest
ruff check .
```
