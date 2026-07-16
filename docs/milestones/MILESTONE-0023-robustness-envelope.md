# Milestone 23 — Robustness Envelope

M23 asks a harder question than “is this decision safe now?”:

> Does the same strategy remain feasible and competitive throughout a bounded uncertainty region?

The milestone stress-tests the M19 strategy using the M17 Digital Twin and publishes a deterministic
certificate containing the complete uncertainty envelope digest. The included demonstration evaluates
81 variants formed from photovoltaic, load, temperature, and tariff perturbations.

## Command

```powershell
py -m heos.robustness
```

Artifacts are written to `~/.heos/robustness/latest`:

- `report.txt`
- `robustness.json`
- `certificate.sha256`

## Safety

M23 is advisory. It never commands devices and never bypasses any release or safety layer.
