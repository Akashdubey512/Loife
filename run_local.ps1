# reServe AI - PowerShell Platform Launcher
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  reServe AI - Smart Food Waste & Redistribution" -ForegroundColor Cyan
Write-Host "  Smart India Hackathon (SIH 2026) Enterprise Edition" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

Write-Host "Launching Backend API on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 3

Write-Host "Launching Frontend Console on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nAll services active!" -ForegroundColor Green
Write-Host "Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs:  http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
