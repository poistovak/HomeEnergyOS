# HEOS M17 installation

The package is a drop-in patch for `C:\HEOS\HomeEnergyOS`.

1. Keep this ZIP outside the repository, normally in Downloads.
2. Extract it to a temporary directory.
3. Run PowerShell in that directory.
4. Execute:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\apply_m17.ps1
```

The installer copies only files under `payload`. Installer files are not copied into Git.
It then runs the full pytest suite and Ruff.
