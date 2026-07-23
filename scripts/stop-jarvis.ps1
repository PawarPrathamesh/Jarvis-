$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $root "backend\.venv\Scripts\python.exe"

$pythonProcesses = Get-Process | Where-Object {
  $_.ProcessName -like "*python*" -and $_.Path -eq $backendPython
}

$nodeProcessIds = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -eq "node.exe" -and $_.CommandLine -like "*F:\Projects\jarvis\frontend*"
} | Select-Object -ExpandProperty ProcessId

$nodeProcesses = Get-Process | Where-Object {
  $_.Id -in $nodeProcessIds
}

foreach ($process in $pythonProcesses) {
  Stop-Process -Id $process.Id
  Write-Host "Stopped backend process $($process.Id)"
}

foreach ($process in $nodeProcesses) {
  Stop-Process -Id $process.Id
  Write-Host "Stopped node process $($process.Id)"
}

if (-not $pythonProcesses -and -not $nodeProcesses) {
  Write-Host "No Jarvis backend/frontend processes found."
}
