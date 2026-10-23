# Pistacho QA Service - Run Script (Windows PowerShell)
# Place model in artifacts/distilbert-squad2/, set QA_API_TOKEN, run this script

$ErrorActionPreference = "Stop"

if (-not $env:QA_API_TOKEN) {
    Write-Host "QA_API_TOKEN is not set. Set it first:" -ForegroundColor Red
    Write-Host "  `$env:QA_API_TOKEN = '<your-agreed-token>'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Pistacho QA Service on http://0.0.0.0:8000" -ForegroundColor Green
uvicorn app:app --host 0.0.0.0 --port 8000
