$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendUrl = "http://127.0.0.1:8000/"
$backendHealthUrl = "http://127.0.0.1:8001/api/v1/health"
$appUrl = "http://127.0.0.1:8000/"
$venvPath = Join-Path $root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$requirementsPath = Join-Path $root "backend\requirements.txt"
$envExamplePath = Join-Path $root ".env.example"
$envPath = Join-Path $root ".env"

function Get-PythonBootstrapCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ FilePath = "py"; ArgumentList = @("-3") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ FilePath = "python"; ArgumentList = @() }
    }
    throw "Python 3 is not installed or not available on PATH."
}

function Ensure-Command {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Hint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is not available. $Hint"
    }
}

function Ensure-EnvFile {
    if (-not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
        Write-Host "Creating .env from .env.example ..."
        Copy-Item -Path $envExamplePath -Destination $envPath
    }
}

function Wait-ForUrl {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)

    return $false
}

function Ensure-VenvPython {
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $bootstrap = Get-PythonBootstrapCommand
    Write-Host "Creating virtual environment ..."
    & $bootstrap.FilePath @($bootstrap.ArgumentList + @("-m", "venv", $venvPath))

    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment creation did not produce $venvPython"
    }

    return $venvPython
}

Ensure-Command -Name "node" -Hint "Install Node.js and rerun this script."
Ensure-EnvFile
$pythonPath = Ensure-VenvPython

Write-Host "Installing backend dependencies ..."
& $pythonPath -m pip install --disable-pip-version-check -r $requirementsPath | Out-Null

$frontendWasRunning = Wait-ForUrl -Url $frontendUrl -TimeoutSeconds 2
if (-not $frontendWasRunning) {
    Write-Host "Starting front-end on $frontendUrl"
    Start-Process -WorkingDirectory $root -FilePath "node" -ArgumentList @("server.js") | Out-Null
}
else {
    Write-Host "Front-end already responding on $frontendUrl"
}

$backendWasRunning = Wait-ForUrl -Url $backendHealthUrl -TimeoutSeconds 2
if (-not $backendWasRunning) {
    Write-Host "Starting backend on http://127.0.0.1:8001"
    Start-Process -WorkingDirectory $root -FilePath $pythonPath -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--reload", "--port", "8001") | Out-Null
}
else {
    Write-Host "Backend already responding on http://127.0.0.1:8001"
}

if (-not (Wait-ForUrl -Url $frontendUrl -TimeoutSeconds 20)) {
    throw "Front-end did not become available at $frontendUrl"
}

if (-not (Wait-ForUrl -Url $backendHealthUrl -TimeoutSeconds 30)) {
    throw "Backend did not become healthy at $backendHealthUrl"
}

Start-Process $appUrl | Out-Null
Write-Host "Labib is ready for local testing."
Write-Host "Front-end: $frontendUrl"
Write-Host "Back-end health: $backendHealthUrl"
