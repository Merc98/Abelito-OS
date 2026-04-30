# ABEL OS+ Launcher Script
Write-Host "🚀 Launching ABEL OS+ Environment..." -ForegroundColor Cyan

# Check for NATS
Write-Host "[-] Checking NATS Connection..." -ForegroundColor Yellow
$NATS_URL = $env:NATS_URL -or "nats://localhost:4222"

# Start CEO API
Write-Host "[-] Starting CEO API (FastAPI)..." -ForegroundColor Yellow
Start-Process python -ArgumentList "-m uvicorn apps.ceo_api.main:app --reload --port 8000" -WindowStyle Normal

# Start Navigator Service
Write-Host "[-] Starting Navigator Service..." -ForegroundColor Yellow
Start-Process python -ArgumentList "-m uvicorn apps.navigator:app --port 8001" -WindowStyle Normal

# Start OSINT Orchestrator
Write-Host "[-] Starting OSINT Orchestrator..." -ForegroundColor Yellow
Start-Process python -ArgumentList "apps/osint_orchestrator/main.py" -WindowStyle Normal

Write-Host "✅ Systems Online!" -ForegroundColor Green
Write-Host "   CEO API: http://localhost:8000"
Write-Host "   Navigator: http://localhost:8001"
Write-Host "   Desktop App: cd apps/desktop; npm start"
