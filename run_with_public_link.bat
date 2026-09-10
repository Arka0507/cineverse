@echo off
title Cineverse with Public Link
cd /d "%~dp0"

echo ===================================================
echo     Starting Cineverse with Public Cloudflare Link  
echo ===================================================

echo [1/3] Starting FastAPI Backend on port 8000...
start "Cineverse Backend (:8000)" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo [2/3] Starting Local Frontend on port 3000...
start "Cineverse Frontend (:3000)" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe scripts/preview.py"

echo [3/3] Starting Cloudflare Public Tunnel...
echo Look for the 'https://...trycloudflare.com' link in the window that opens!
start "Cineverse Public Tunnel" cmd /k "cd /d "%~dp0" && .\cloudflared.exe tunnel --url http://127.0.0.1:8000"

echo.
echo ===================================================
echo All services started!
echo Local Link: http://localhost:3000
echo Check the Cloudflare window for your live Public Link!
echo ===================================================
timeout /t 2 >nul
start http://localhost:3000
