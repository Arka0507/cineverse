@echo off
title Cineverse Launcher
cd /d "%~dp0"

echo ===================================================
echo           Starting Cineverse Movie Platform        
echo ===================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000...
start "Cineverse Backend (:8000)" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend on http://localhost:3000...
start "Cineverse Frontend (:3000)" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe scripts/preview.py"

echo.
echo ===================================================
echo Cineverse is now online!
echo Local URL: http://localhost:3000
echo ===================================================
timeout /t 2 >nul
start http://localhost:3000
