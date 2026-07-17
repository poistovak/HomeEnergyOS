param(
    [Parameter(Mandatory=$false)]
    [string]$RepositoryPath = ".\HomeEnergyOS"
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $RepositoryPath)) {
    throw "Repository path not found: $RepositoryPath"
}

Copy-Item "$SourceRoot\src\heos\resilience" "$RepositoryPath\src\heos" -Recurse -Force
Copy-Item "$SourceRoot\tests\test_resilience.py" "$RepositoryPath\tests" -Force
Copy-Item "$SourceRoot\CHANGELOG_MILESTONE_24.md" "$RepositoryPath" -Force

Push-Location $RepositoryPath
try {
    python -m pytest
}
finally {
    Pop-Location
}
