[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Python environment not found at $pythonExe" -ForegroundColor Red
    exit 1
}

$prevPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = "$backendDir;$env:PYTHONPATH"

try {
    Write-Host "================ HOT SQLITE DATABASE BACKUP (BACKUP.bat) ================" -ForegroundColor Cyan
    & $pythonExe -m app.commands.backup_helper create
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        Write-Host "Backup completed and verified in backend/.local/backups/" -ForegroundColor Green
    } else {
        Write-Host "Backup failed. See errors above." -ForegroundColor Red
    }
    exit $exitCode
} finally {
    $env:PYTHONPATH = $prevPythonPath
}