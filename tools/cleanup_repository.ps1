$ErrorActionPreference = "Stop"

Write-Host "HEOS repository cleanup" -ForegroundColor Cyan

$paths = @(
    "src\heos\core\executor.py.py",
    "src\heos\core\normalizer.py.py",
    "src\heos\core\pipeline.py.py",
    "src\heos\core\validator.py.py"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "Removed legacy invalid filename: $path"
    }
}

Get-ChildItem -Path . -Directory -Recurse -Force |
    Where-Object { $_.Name -eq "__pycache__" -or $_.Name -eq ".pytest_cache" -or $_.Name -eq ".ruff_cache" } |
    Remove-Item -Recurse -Force

Get-ChildItem -Path . -File -Recurse -Force -Include *.pyc,*.pyo |
    Remove-Item -Force

Write-Host "Cleanup complete. Review GitHub Desktop changes before committing." -ForegroundColor Green
