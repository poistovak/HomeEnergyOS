# HEOS M28 — Result Verification

M28 verifies that a real device reached the result requested by HEOS. It evaluates time-ordered observations, absolute and relative tolerances, evidence quality, minimum sample count and a trailing stability window.

## Outcomes

- `SUCCESS`
- `PARTIAL`
- `FAILED`
- `TIMEOUT`
- `UNKNOWN`

## Follow-up actions

- `ACCEPT`
- `RETRY`
- `ROLLBACK`
- `ESCALATE`

## Example

```python
from heos.result_verification import (
    Observation,
    ResultExpectation,
    ResultVerificationEngine,
)

engine = ResultVerificationEngine()
decision = engine.verify(
    ResultExpectation(
        command_id="cmd-028",
        target="wattpilot.charging_power",
        expected_value=2300,
        absolute_tolerance=250,
        deadline=20,
        stability_samples=2,
        minimum_samples=2,
        rollback_supported=True,
    ),
    [
        Observation("wattpilot.charging_power", 2250, 8, "home_assistant"),
        Observation("wattpilot.charging_power", 2310, 10, "home_assistant"),
    ],
)
```

## Install

```powershell
Expand-Archive .\HEOS_M28_Result_Verification.zip -DestinationPath .\M28 -Force
cd .\M28\HEOS_M28_Result_Verification
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\INSTALL_M28.ps1 -Repo "C:\HEOS\HomeEnergyOS"
```
