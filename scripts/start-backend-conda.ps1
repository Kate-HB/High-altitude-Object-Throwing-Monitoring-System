$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = "D:\Soft\Conda\python.exe"

# Guard: verify Conda Python has required packages
$check = & $Python -c "import fastapi, uvicorn, torch, ultralytics, cv2; print('ok')" 2>&1
if ($check -ne "ok") {
    Write-Host "Conda Python missing packages. Run:" -ForegroundColor Yellow
    Write-Host "  D:\Soft\Conda\python.exe -m pip install fastapi uvicorn[standard] pydantic pydantic-settings python-multipart httpx2" -ForegroundColor Yellow
    exit 1
}

& $Python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
exit $LASTEXITCODE
