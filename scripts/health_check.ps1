# Health Check script for TikTok Shop Affiliate Trend Hunter
[CmdletBinding()]
param(
    [ValidateSet("All", "Frontend", "Backend")]
    [string]$Target = "All",
    [int]$TimeoutSec = 25,
    [switch]$WaitReady,
    [switch]$Quiet
)

$rootDir = Split-Path -Parent $PSScriptRoot
$logFile = Join-Path (Join-Path $rootDir "logs") "services.log"

$checkBackend = ($Target -eq "All" -or $Target -eq "Backend")
$checkFrontend = ($Target -eq "All" -or $Target -eq "Frontend")

$backendHealthy = $false
$frontendHealthy = $false
$backendDetails = ""
$frontendDetails = ""

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

function Test-Backend {
    $uris = @("http://127.0.0.1:8000/api/health", "http://localhost:8000/api/health")
    foreach ($uri in $uris) {
        try {
            $res = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($res.status -eq "ok" -and $res.database -eq "connected") {
                $script:backendDetails = "Status: $($res.status) | DB: $($res.database) | Region: $($res.region)"
                return $true
            }
        } catch {
            $script:backendDetails = "Error: $($_.Exception.Message)"
        }
    }
    return $false
}

function Test-Frontend {
    $uris = @("http://localhost:3000", "http://127.0.0.1:3000")
    foreach ($uri in $uris) {
        try {
            $res = Invoke-WebRequest -Uri $uri -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($res.StatusCode -eq 200) {
                $script:frontendDetails = "HTTP 200 OK (Next.js Dashboard)"
                return $true
            }
        } catch {
            $script:frontendDetails = "Error: $($_.Exception.Message)"
        }
    }
    return $false
}

if ($WaitReady) {
    if (-not $Quiet) {
        Write-Host "Dang kiem tra tinh trang san sang [$Target] (Timeout: ${TimeoutSec}s)..." -ForegroundColor Cyan
    }
    
    while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSec) {
        if ($checkBackend -and (-not $backendHealthy)) {
            $backendHealthy = Test-Backend
        } else {
            $backendHealthy = $true
        }

        if ($checkFrontend -and (-not $frontendHealthy)) {
            $frontendHealthy = Test-Frontend
        } else {
            $frontendHealthy = $true
        }

        if ((-not $checkBackend -or $backendHealthy) -and (-not $checkFrontend -or $frontendHealthy)) {
            break
        }
        Start-Sleep -Milliseconds 800
    }
} else {
    if ($checkBackend) { $backendHealthy = Test-Backend } else { $backendHealthy = $true }
    if ($checkFrontend) { $frontendHealthy = Test-Frontend } else { $frontendHealthy = $true }
}

$allOk = $true
if ($checkBackend -and (-not $backendHealthy)) { $allOk = $false }
if ($checkFrontend -and (-not $frontendHealthy)) { $allOk = $false }

$timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
if (Test-Path (Split-Path $logFile -Parent)) {
    $backendLogMsg = if ($checkBackend) { "Backend: $(if ($backendHealthy) {'OK'} else {'FAIL'}) ($backendDetails)" } else { "Backend: SKIPPED" }
    $frontendLogMsg = if ($checkFrontend) { "Frontend: $(if ($frontendHealthy) {'OK'} else {'FAIL'}) ($frontendDetails)" } else { "Frontend: SKIPPED" }
    Add-Content -Path $logFile -Value "[$timestamp] [HEALTH] $backendLogMsg | $frontendLogMsg" -ErrorAction SilentlyContinue
}

if (-not $Quiet) {
    Write-Host ""
    Write-Host "================== KET QUA HEALTH CHECK ==================" -ForegroundColor Cyan
    if ($checkBackend) {
        if ($backendHealthy) {
            Write-Host " [OK]   Backend FastAPI (Port 8000): $backendDetails" -ForegroundColor Green
        } else {
            Write-Host " [FAIL] Backend FastAPI (Port 8000): $backendDetails" -ForegroundColor Red
        }
    }
    if ($checkFrontend) {
        if ($frontendHealthy) {
            Write-Host " [OK]   Frontend Next.js (Port 3000): $frontendDetails" -ForegroundColor Green
        } else {
            Write-Host " [FAIL] Frontend Next.js (Port 3000): $frontendDetails" -ForegroundColor Red
        }
    }
    Write-Host "==========================================================" -ForegroundColor Cyan
}

if ($allOk) {
    exit 0
} else {
    exit 1
}
