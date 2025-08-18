$ErrorActionPreference = "Stop"
$VenvPath = Join-Path $PSScriptRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts" "python.exe"
$env:PYTHONPATH = $PSScriptRoot

Write-Host "Running tests..."
& $PythonPath -m pytest tests/test_debug.py -v
