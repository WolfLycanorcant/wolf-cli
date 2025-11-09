# Wolf CLI Launcher Script
# Quick wrapper to activate venv and run Wolf CLI

$scriptPath = $PSScriptRoot
$venvPath = Join-Path $scriptPath "venv\Scripts\Activate.ps1"
$pythonPath = Join-Path $scriptPath "venv\Scripts\python.exe"

# Check if venv exists
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate venv and run Wolf CLI with all arguments
& $venvPath
& $pythonPath -m wolf.cli_wrapper $args
