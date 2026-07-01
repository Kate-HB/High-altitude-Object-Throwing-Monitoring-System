$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
& $Python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
exit $LASTEXITCODE
