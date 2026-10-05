[CmdletBinding()]
param(
    [string]$CandidatePath,
    [switch]$Recover
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$env:PYTHONPATH = "$backendDir;$env:PYTHONPATH"
$pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
$targetDb = Join-Path $backendDir 'affiliate.db'
$backupsDir = Join-Path $backendDir '.local\backups'
$restoreDir = Join-Path $backendDir '.local\restore'

if (-not (Test-Path $backupsDir)) {
    New-Item -ItemType Directory -Path $backupsDir -Force | Out-Null
}
if (-not (Test-Path $restoreDir)) {
    New-Item -ItemType Directory -Path $restoreDir -Force | Out-Null
}

if ($Recover) {
    Write-Host "================ RESTORE RECOVERY MODE (--recover) ================" -ForegroundColor Cyan
    & $pythonExe -m app.commands.restore_helper recover
    $res = $LASTEXITCODE
    if ($res -eq 0) {
        Write-Host "Recovery completed. Ordinary startup is unblocked." -ForegroundColor Green
    } else {
        Write-Host "Recovery failed. Please inspect backend/.local/restore/manifest.json." -ForegroundColor Red
    }
    exit $res
}

if (-not $CandidatePath) {
    & $pythonExe -m app.commands.restore_helper list-candidates
    exit 1
}

$candidateFull = [System.IO.Path]::GetFullPath($CandidatePath)
if (-not (Test-Path -LiteralPath $candidateFull)) {
    Write-Host "ERROR: Backup file '$CandidatePath' does not exist." -ForegroundColor Red
    exit 1
}

Write-Host "================ OFFLINE DATABASE RESTORE WORKFLOW ================" -ForegroundColor Cyan
Write-Host "Candidate file: $candidateFull"

# STEP 1: VALIDATE CANDIDATE BEFORE STOPPING SERVICES
Write-Host "[1/6] Validating candidate backup file integrity and compatibility..." -ForegroundColor Yellow
& $pythonExe -m app.commands.restore_helper validate-candidate "$candidateFull"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ABORTED: Candidate file is invalid. Services were not stopped and remain unaffected." -ForegroundColor Red
    exit 1
}

# Initialize transaction manifest
& $pythonExe -m app.commands.restore_helper init-manifest "$candidateFull"

# STEP 2: QUIESCE SERVICES (BACKEND & FRONTEND)
Write-Host "[2/6] Quiescing services (Backend & Frontend)..." -ForegroundColor Yellow
& $pythonExe -m app.commands.restore_helper update-manifest STOPPING_SERVICES
& "$PSScriptRoot\stop_services.ps1" -Target All -Quiet

# STEP 3: CREATE VALIDATED PRE-RESTORE SAFETY BACKUP
Write-Host "[3/6] Creating validated safety backup of active database using SQLite backup API..." -ForegroundColor Yellow
$safetyFilename = (& $pythonExe -m app.commands.restore_helper safety-filename).Trim()
$safetyBackupPath = Join-Path $backupsDir $safetyFilename

& $pythonExe -m app.commands.restore_helper create-safety-backup "$targetDb" "$safetyBackupPath"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create validated safety backup. Aborting restore..." -ForegroundColor Red
    & $pythonExe -m app.commands.restore_helper update-manifest ABORTED --error "Failed to create pre-restore safety backup"
    & "$PSScriptRoot\start_services.ps1" -Target All
    exit 1
}
& $pythonExe -m app.commands.restore_helper update-manifest SAFETY_BACKUP_CREATED --safety-backup "$safetyBackupPath"

# STEP 4: ATOMIC DATABASE REPLACEMENT
Write-Host "[4/6] Replacing database with candidate file..." -ForegroundColor Yellow
& $pythonExe -m app.commands.restore_helper update-manifest REPLACEMENT_STARTED
& $pythonExe -m app.commands.restore_helper replace-db "$candidateFull" "$targetDb"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Database replacement failed! Rolling back to safety backup..." -ForegroundColor Red
    & $pythonExe -m app.commands.restore_helper rollback "$safetyBackupPath" "$targetDb"
    & $pythonExe -m app.commands.restore_helper update-manifest ROLLED_BACK --error "Replacement failed; rolled back to safety backup"
    & "$PSScriptRoot\start_services.ps1" -Target All
    exit 1
}

# STEP 5: RESTART SERVICES & RUN RECONCILIATION
Write-Host "[5/6] Restarting services and running alert catch-up..." -ForegroundColor Yellow
try {
    & "$PSScriptRoot\start_services.ps1" -Target All
} catch {
    Write-Host "ERROR: Service restart failed! Rolling back..." -ForegroundColor Red
    & "$PSScriptRoot\stop_services.ps1" -Target All -Quiet
    & $pythonExe -m app.commands.restore_helper rollback "$safetyBackupPath" "$targetDb"
    & $pythonExe -m app.commands.restore_helper update-manifest ROLLED_BACK --error "Restart failed; rolled back"
    & "$PSScriptRoot\start_services.ps1" -Target All
    exit 1
}

# STEP 6: POST-RESTORE HEALTH CHECK
Write-Host "[6/6] Verifying system health..." -ForegroundColor Yellow
$healthOk = $false
try {
    $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 10 -ErrorAction Stop
    if ($resp.status -eq "ok" -and $resp.database -eq "connected") {
        $healthOk = $true
    }
} catch {
    $healthOk = $false
}

if (-not $healthOk) {
    Write-Host "ERROR: Health check failed! Rolling back..." -ForegroundColor Red
    & "$PSScriptRoot\stop_services.ps1" -Target All -Quiet
    & $pythonExe -m app.commands.restore_helper rollback "$safetyBackupPath" "$targetDb"
    & $pythonExe -m app.commands.restore_helper update-manifest ROLLED_BACK --error "Post-restore health check failed; rolled back"
    & "$PSScriptRoot\start_services.ps1" -Target All
    exit 1
}

& $pythonExe -m app.commands.restore_helper update-manifest COMPLETED
Write-Host "================ RESTORE COMPLETED SUCCESSFULLY ================" -ForegroundColor Green
Write-Host "Database restored and verified." -ForegroundColor Green
exit 0
