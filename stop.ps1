$ErrorActionPreference = "SilentlyContinue"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runDir = Join-Path $root ".run"

function Stop-ProcessTree {
  param (
    [int]$ParentId
  )

  $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$ParentId" -ErrorAction SilentlyContinue
  foreach ($child in $children) {
    Stop-ProcessTree -ParentId $child.ProcessId
  }

  Stop-Process -Id $ParentId -Force -ErrorAction SilentlyContinue
}

function Stop-ByPidFile {
  param (
    [string]$pidPath
  )

  if (Test-Path $pidPath) {
    $pid = Get-Content $pidPath | Select-Object -First 1
    if ($pid) {
      Stop-ProcessTree -ParentId ([int]$pid)
    }
    Remove-Item $pidPath -ErrorAction SilentlyContinue
  }
}

Stop-ByPidFile -pidPath (Join-Path $runDir "backend.pid")
Stop-ByPidFile -pidPath (Join-Path $runDir "frontend.pid")

Write-Host "Arret OK. PIDs nettoyes."
