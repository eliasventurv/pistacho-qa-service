param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not $env:QA_API_TOKEN) { throw 'Set QA_API_TOKEN in this terminal before starting. Never put the token in source code.' }
if (-not (Test-Path 'artifacts/distilbert-squad2/training_provenance.json')) { throw 'No trained model found. Run .\train.ps1 first.' }
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port $Port --workers 1
exit $LASTEXITCODE
