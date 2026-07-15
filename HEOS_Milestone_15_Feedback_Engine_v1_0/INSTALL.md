# HEOS Milestone 15 installation

This ZIP is a **drop-in patch**, not a replacement repository.

1. Extract the ZIP.
2. Copy its contents into the root of `C:\HEOS\HomeEnergyOS`.
3. Keep the directory structure (`src`, `tests`, `docs`, `examples`).
4. Run:

```powershell
cd C:\HEOS\HomeEnergyOS
$env:PYTHONPATH = "src"
python -m pytest -q
python -m ruff check .
```

The patch adds only new Milestone 15 files. It does not overwrite M11–M14 source modules.
