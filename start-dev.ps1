$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root ".venv"
$pythonPath = Join-Path $venvPath "Scripts\\python.exe"
$requirementsPath = Join-Path $root "backend\\requirements.txt"

function Ensure-Command {
  param([string]$Name, [string]$Hint)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    Write-Error "$Name is not available. $Hint"
  }
}

Ensure-Command -Name "py" -Hint "Install Python 3 and re-run this script."
Ensure-Command -Name "node" -Hint "Install Node.js and re-run this script."

if (-not (Test-Path $pythonPath)) {
  Write-Host "Creating virtual environment..."
  py -3 -m venv $venvPath
}

Write-Host "Installing backend dependencies..."
& $pythonPath -m pip install -r $requirementsPath | Out-Null

Write-Host "Starting front-end on http://localhost:8000 ..."
Start-Process -WorkingDirectory $root -FilePath "node" -ArgumentList "server.js"

Write-Host "Starting backend on http://localhost:8001 ..."
Start-Process -WorkingDirectory $root -FilePath $pythonPath -ArgumentList "-m uvicorn backend.app.main:app --reload --port 8001"

Start-Sleep -Seconds 2
Start-Process "http://localhost:8000"

Write-Host "If the browser did not open, go to http://localhost:8000"
