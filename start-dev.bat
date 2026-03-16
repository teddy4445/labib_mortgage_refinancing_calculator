@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0
cd /d "%ROOT%"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" not found. Install Python 3 and try again.
  exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js not found. Install Node.js and try again.
  exit /b 1
)

if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv "%ROOT%\.venv"
)

echo Installing backend dependencies...
"%ROOT%\.venv\Scripts\python.exe" -m pip install -r "%ROOT%\backend\requirements.txt" >nul

echo Starting front-end on http://localhost:8000 ...
start "" node "%ROOT%\server.js"

echo Starting backend on http://localhost:8001 ...
start "" "%ROOT%\.venv\Scripts\python.exe" -m uvicorn backend.app.main:app --reload --port 8001

timeout /t 2 >nul
start "" "http://localhost:8000"

echo If the browser did not open, go to http://localhost:8000
endlocal
