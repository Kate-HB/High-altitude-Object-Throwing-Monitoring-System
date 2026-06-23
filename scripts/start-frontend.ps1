$ErrorActionPreference = "Stop"
$FrontendDir = Join-Path (Split-Path -Parent $PSScriptRoot) "frontend"
Set-Location $FrontendDir
npm run dev
