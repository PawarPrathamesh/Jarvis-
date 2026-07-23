param(
  [string]$HostIp = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

if (-not $HostIp) {
  $ipconfig = ipconfig
  $HostIp = ($ipconfig | Select-String -Pattern "IPv4 Address.*: (\d+\.\d+\.\d+\.\d+)" | Select-Object -First 1).Matches.Groups[1].Value
}

if (-not $HostIp) {
  throw "Could not detect Wi-Fi IP. Run scripts\start-wifi.ps1 -HostIp YOUR_IP"
}

Start-Process -FilePath (Join-Path $backend ".venv\Scripts\python.exe") `
  -ArgumentList "-m uvicorn app.main:app --host $HostIp --port 8000" `
  -WorkingDirectory $backend `
  -WindowStyle Hidden

Start-Process -FilePath "npm" `
  -ArgumentList "run dev -- --host 0.0.0.0 --port 5173" `
  -WorkingDirectory $frontend `
  -WindowStyle Hidden

Write-Host "Jarvis phone dashboard: http://$HostIp`:5173"
Write-Host "Jarvis Wi-Fi backend:   http://$HostIp`:8000/health"
