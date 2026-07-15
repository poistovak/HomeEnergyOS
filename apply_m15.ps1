param(
    [string]$RepositoryRoot = "C:\HEOS\HomeEnergyOS"
)

$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "M15 patch: $PatchRoot" -ForegroundColor Cyan
Write-Host "HEOS repo:  $RepositoryRoot" -ForegroundColor Cyan

if (-not (Test-Path (Join-Path $PatchRoot "src\heos\feedback\__init__.py"))) {
    throw "This is not a complete M15 patch: src\heos\feedback\__init__.py is missing."
}

if (-not (Test-Path (Join-Path $RepositoryRoot "pyproject.toml"))) {
    throw "HEOS repository not found at $RepositoryRoot (pyproject.toml is missing)."
}

foreach ($directory in @("src", "tests", "docs", "examples")) {
    $source = Join-Path $PatchRoot $directory
    $destination = Join-Path $RepositoryRoot $directory
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Copy-Item -Path (Join-Path $source "*") -Destination $destination -Recurse -Force
}

Copy-Item -Path (Join-Path $PatchRoot "CHANGELOG_MILESTONE_15.md") -Destination $RepositoryRoot -Force

Push-Location $RepositoryRoot
try {
    $env:PYTHONPATH = "src"
    Write-Host "Running tests..." -ForegroundColor Yellow
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "pytest failed with exit code $LASTEXITCODE" }

    Write-Host "Running Ruff..." -ForegroundColor Yellow
    python -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed with exit code $LASTEXITCODE" }

    Write-Host "M15 installed and validated." -ForegroundColor Green
}
finally {
    Pop-Location
}
