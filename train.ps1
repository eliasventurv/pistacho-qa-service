param([string]$Resume = '')
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = "$PSScriptRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw 'Run setup.ps1 first.' }
$arguments = @('-m', 'src.train')
if ($Resume) { $arguments += @('--resume', $Resume) }
& $python @arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m src.threshold --device cuda
exit $LASTEXITCODE
