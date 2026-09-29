@echo off
TITLE reServe AI - Enterprise Platform Launcher
echo ========================================================
echo   reServe AI - Smart Food Waste & Redistribution Platform
echo   Smart India Hackathon (SIH 2026) Enterprise Edition
echo ========================================================
echo.

echo Starting reServe AI FastAPI Backend on http://localhost:8000 ...
start "reServe AI Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo Starting reServe AI React Enterprise Console on http://localhost:3000 ...
start "reServe AI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo [OK] All services launched!
echo - Frontend Console:  http://localhost:3000
echo - Swagger API Docs:  http://localhost:8000/api/v1/docs
echo - WebSocket Stream:  ws://localhost:8000/ws/telemetry
echo ========================================================
