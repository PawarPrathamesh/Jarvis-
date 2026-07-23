$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

Start-Process -FilePath (Join-Path $backend ".venv\Scripts\python.exe") `
  -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000" `
  -WorkingDirectory $backend `
  -WindowStyle Hidden

Start-Process -FilePath "npm" `
  -ArgumentList "run dev -- --host 127.0.0.1 --port 5173" `
  -WorkingDirectory $frontend `
  -WindowStyle Hidden

Write-Host "Jarvis local dashboard: http://127.0.0.1:5173"
Write-Host "Jarvis backend:         http://127.0.0.1:8000/health"
