param(
    [string]$RepositoryRoot = "C:\HEOS\HomeEnergyOS"
)

$ErrorActionPreference = "Stop"
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path (Join-Path $RepositoryRoot "pyproject.toml"))) {
    throw "HEOS repository not found at $RepositoryRoot"
}

$items = @("src", "tests", "docs", "examples", "CHANGELOG_MILESTONE_15.md")
foreach ($item in $items) {
    Copy-Item -Path (Join-Path $PatchRoot $item) -Destination $RepositoryRoot -Recurse -Force
}

Push-Location $RepositoryRoot
try {
    $env:PYTHONPATH = "src"
    python -m pytest -q
    python -m ruff check .
}
finally {
    Pop-Location
}
