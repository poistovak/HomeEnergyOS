param(
    [Parameter(Mandatory=$false)]
    [string]$RepositoryPath = ".\HomeEnergyOS"
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $RepositoryPath)) {
    throw "Repository path not found: $RepositoryPath"
}

Copy-Item "$SourceRoot\src\heos\continuity" `
    "$RepositoryPath\src\heos" -Recurse -Force
Copy-Item "$SourceRoot\tests\test_continuity.py" `
    "$RepositoryPath\tests" -Force
Copy-Item "$SourceRoot\CHANGELOG_MILESTONE_25.md" `
    "$RepositoryPath" -Force

Push-Location $RepositoryPath
try {
    python -m pytest
    ruff check .
}
finally {
    Pop-Location
}
