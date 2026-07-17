# HEOS M26 — Execution Supervisor

M26 converts an M25 continuity directive into a deterministic, bounded and auditable execution command.
It validates deadlines and approvals, caps retry attempts, emits a SHA-256 certificate and maintains a tamper-evident ledger.

## Install

```powershell
Expand-Archive .\HEOS_M26_Execution_Supervisor.zip -DestinationPath .\M26 -Force
Copy-Item .\M26\* .\HomeEnergyOS -Recurse -Force
cd .\HomeEnergyOS
python -m pytest
ruff check .
```
