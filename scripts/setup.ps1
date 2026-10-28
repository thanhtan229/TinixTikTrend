# One-time setup for a fresh machine.
# Prepares the backend virtualenv, frontend dependencies, and Playwright Chromium.
# Idempotent: safe to re-run. Does not start services; use start.bat afterwards.
param(
    [switch]$SkipBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'

function Write-Step($message) { Write-Host "`n==> $message" -ForegroundColor Cyan }
function Fail($message) { Write-Host "[SETUP FAILED] $message" -ForegroundColor Red; exit 1 }

# 1. Python 3.11 (the project's validated runtime)
Write-Step 'Checking Python 3.11'
# Windows PowerShell 5.1 turns native stderr into terminating errors under 'Stop',
# so probes run with 'Continue' locally and are judged by $LASTEXITCODE and output.
$pyExe = $null
$pyArgs = @()
if (Get-Command py.exe -ErrorAction SilentlyContinue) {
    $savedPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & py.exe -3.11 --version *> $null } finally { $ErrorActionPreference = $savedPref }
    if ($LASTEXITCODE -eq 0) { $pyExe = 'py.exe'; $pyArgs = @('-3.11') }
}
if (-not $pyExe -and (Get-Command python.exe -ErrorAction SilentlyContinue)) {
    $savedPref = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { $version = & python.exe --version 2>&1 } finally { $ErrorActionPreference = $savedPref }
    # The Microsoft Store alias on PATH exits non-zero and prints a notice; it must not match.
    if ($LASTEXITCODE -eq 0 -and "$version" -match '^Python 3\.11\.') { $pyExe = 'python.exe' }
}
if (-not $pyExe) {
    Fail 'Python 3.11 not found. Install Python 3.11 from python.org (tick "Add to PATH") or via the py launcher, then re-run.'
}
Write-Host "Using Python 3.11: $pyExe $($pyArgs -join ' ')"

# 2. Node.js (required by the Next.js frontend)
Write-Step 'Checking Node.js'
if (-not (Get-Command node.exe -ErrorAction SilentlyContinue)) {
    Fail 'Node.js not found. Install the LTS release from nodejs.org, then re-run.'
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Fail 'npm not found. Reinstall Node.js from nodejs.org so npm is included, then re-run.'
}
$nodeVersion = & node.exe --version
if ($LASTEXITCODE -ne 0) { Fail 'node.exe failed to run. Reinstall Node.js, then re-run.' }
Write-Host "Node: $nodeVersion"

# 3. Backend virtualenv and dependencies
Write-Step 'Preparing backend virtualenv'
$venvPython = Join-Path $backendDir '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
    # A venv built by another Python version would silently run the wrong interpreter.
    $venvVersion = & $venvPython --version 2>&1
    if ($LASTEXITCODE -ne 0 -or "$venvVersion" -notmatch '^Python 3\.11\.') {
        Fail "Existing backend\.venv is not Python 3.11 ($venvVersion). Delete backend\.venv and re-run setup."
    }
} else {
    & $pyExe @pyArgs -m venv (Join-Path $backendDir '.venv')
    if ($LASTEXITCODE -ne 0) { Fail 'Failed to create backend .venv.' }
}
& $venvPython -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail 'pip upgrade failed.' }
& $venvPython -m pip install --quiet -r (Join-Path $backendDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Fail 'Installing backend requirements failed.' }

# 4. Playwright Chromium (used by the TikTok collector)
if ($SkipBrowser) {
    Write-Step 'Skipping Playwright browser install (-SkipBrowser)'
} else {
    Write-Step 'Installing Playwright Chromium'
    & $venvPython -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { Fail 'Playwright Chromium install failed. Re-run, or use -SkipBrowser to skip collection features.' }
}

# 5. Frontend dependencies from the lockfile
Write-Step 'Installing frontend dependencies (npm ci)'
Push-Location $frontendDir
try {
    & npm.cmd ci
    if ($LASTEXITCODE -ne 0) { Fail 'npm ci failed.' }
} finally {
    Pop-Location
}

Write-Step 'Setup complete'
Write-Host 'Next steps:'
Write-Host '  1. Run start.bat to launch backend and frontend.'
Write-Host '  2. Run healthcheck.bat to verify both services.'
Write-Host '  3. Database and TikTok session are machine-local: restore a backup with RESTORE.bat if you have one, and run CONNECT_TIKTOK.bat to log in.'
exit 0
