$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$EnvFile = Join-Path $RepoRoot ".env"
$EnvExample = Join-Path $RepoRoot ".env.example"

if (-not (Test-Path $Python)) {
    Write-Host "Missing virtual environment: .venv" -ForegroundColor Yellow
    Write-Host "Run:"
    Write-Host "py -3.11 -m venv .venv"
    Write-Host ".venv\Scripts\python.exe -m pip install -U pip"
    Write-Host '.venv\Scripts\python.exe -m pip install -e ".[dev]"'
    exit 1
}

& $Python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host ".venv must use Python 3.11 or newer." -ForegroundColor Red
    Write-Host "Recreate it with:"
    Write-Host "py -3.11 -m venv .venv"
    Write-Host ".venv\Scripts\python.exe -m pip install -U pip"
    Write-Host '.venv\Scripts\python.exe -m pip install -e ".[dev]"'
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "Created .env from .env.example" -ForegroundColor Yellow
        Write-Host "Edit .env before enabling real providers." -ForegroundColor Yellow
    } else {
        Write-Host "Missing .env.example" -ForegroundColor Red
        exit 1
    }
}

& $Python -m app.main
