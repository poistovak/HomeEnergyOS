param(
    [string]$RepoPath = "C:\HEOS\HomeEnergyOS"
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadRoot = Join-Path $PackageRoot "payload"

Write-Host "HEOS Milestone 17 - Digital Twin" -ForegroundColor Cyan
Write-Host "Repository: $RepoPath"

if (-not (Test-Path $RepoPath)) {
    throw "Repository path does not exist: $RepoPath"
}
if (-not (Test-Path $PayloadRoot)) {
    throw "Package payload does not exist: $PayloadRoot"
}

$RequiredM16 = Join-Path $RepoPath "src\heos\memory\models.py"
if (-not (Test-Path $RequiredM16)) {
    throw "M16 House Memory is required: $RequiredM16"
}

$Files = Get-ChildItem $PayloadRoot -Recurse -File
foreach ($File in $Files) {
    $RelativePath = $File.FullName.Substring($PayloadRoot.Length).TrimStart([char[]]'\/')
    $Destination = Join-Path $RepoPath $RelativePath
    $DestinationDirectory = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $DestinationDirectory -Force | Out-Null
    Copy-Item $File.FullName $Destination -Force
    Write-Host "Installed: $RelativePath" -ForegroundColor DarkGray
}

Push-Location $RepoPath
try {
    Write-Host "Running full test suite..." -ForegroundColor Yellow
    py -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed with exit code $LASTEXITCODE"
    }

    Write-Host "Running Ruff..." -ForegroundColor Yellow
    py -m ruff check .
    if ($LASTEXITCODE -ne 0) {
        throw "Ruff failed with exit code $LASTEXITCODE"
    }

    Write-Host "M17 installed and validated." -ForegroundColor Green
    Write-Host "Review before Git commit:" -ForegroundColor Cyan
    git status --short
    git diff --stat
}
finally {
    Pop-Location
}
