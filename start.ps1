$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runDir = Join-Path $root ".run"

if (!(Test-Path $runDir)) {
  New-Item -ItemType Directory -Path $runDir | Out-Null
}

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

$backendCmd = "if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
$backendProc = Start-Process -FilePath "powershell" -WorkingDirectory $backendDir -ArgumentList @("-NoProfile", "-Command", $backendCmd) -PassThru -WindowStyle Normal

$frontendCmd = "npm run dev"
$frontendProc = Start-Process -FilePath "powershell" -WorkingDirectory $frontendDir -ArgumentList @("-NoProfile", "-Command", $frontendCmd) -PassThru -WindowStyle Normal

Set-Content -Path (Join-Path $runDir "backend.pid") -Value $backendProc.Id
Set-Content -Path (Join-Path $runDir "frontend.pid") -Value $frontendProc.Id

Write-Host "Demarrage OK. PIDs enregistres dans .run"
