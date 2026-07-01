$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Join-Path $RepoRoot "showcase-demo"
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Port = 8786
$Url = "http://127.0.0.1:$Port/live2d-prototype/"

if (-not (Test-Path $Python)) {
    Write-Host "Missing virtual environment: .venv" -ForegroundColor Yellow
    Write-Host "Create it first, then install project dependencies:"
    Write-Host "py -3.11 -m venv .venv"
    Write-Host ".venv\Scripts\python.exe -m pip install -U pip"
    Write-Host '.venv\Scripts\python.exe -m pip install -e ".[dev]"'
    exit 1
}

if (-not (Test-Path $ShowcaseRoot)) {
    Write-Host "Missing showcase-demo folder: $ShowcaseRoot" -ForegroundColor Red
    exit 1
}

$Existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($Existing) {
    Write-Host "Port $Port is already in use by process $($Existing.OwningProcess)." -ForegroundColor Yellow
    Write-Host "Open: $Url"
    exit 0
}

Write-Host "Starting Live2D showcase server..."
Write-Host "Open: $Url"
Write-Host "Press Ctrl+C in this terminal to stop the server."
Set-Location $ShowcaseRoot
& $Python -m http.server $Port --bind 127.0.0.1
