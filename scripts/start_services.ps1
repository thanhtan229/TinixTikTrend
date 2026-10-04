[CmdletBinding()]
param([ValidateSet('All','Frontend','Backend')][string]$Target='All', [switch]$RestartOld=$true,
      [switch]$OpenBrowser=$false, [int]$TimeoutSec=60)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\service_common.ps1"
$services = if ($Target -eq 'All') { @('Backend','Frontend') } else { @($Target) }
try {
    # Ownership is checked before stopping anything; a port is never proof of ownership.
    foreach ($service in $services) {
        $port = Get-ServicePort $service
        foreach ($listener in @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)) {
            if (-not (Test-OwnedListener $listener $service)) {
                throw "Port $port belongs to another application (PID $($listener.OwningProcess)); nothing was stopped."
            }
        }
    }
    if ($RestartOld) { & "$PSScriptRoot\stop_services.ps1" -Target $Target -Quiet }
    foreach ($service in $services) {
        $port = Get-ServicePort $service
        if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
            throw "Port $port is still occupied."
        }
        if ($service -eq 'Backend') {
            $workingDir = Join-Path $projectRoot 'backend'
            $executable = Join-Path $workingDir '.venv\Scripts\python.exe'
            $arguments = @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000')
        } else {
            $workingDir = Join-Path $projectRoot 'frontend'
            $executable = (Get-Command node.exe).Source
            $entry = Join-Path $workingDir 'node_modules\next\dist\bin\next'
            $arguments = @(('"'+$entry+'"'),'dev','--hostname','127.0.0.1','--port','3000')
        }
        $name = $service.ToLower()
        $oldDist = $env:NEXT_DIST_DIR
        try {
            if ($service -eq 'Frontend') { $env:NEXT_DIST_DIR = '.next-dev' }
            $process = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $workingDir -WindowStyle Hidden `
                -RedirectStandardOutput (Join-Path $serviceLogs "$name.out.log") -RedirectStandardError (Join-Path $serviceLogs "$name.err.log") -PassThru
        } finally { $env:NEXT_DIST_DIR = $oldDist }
        @{ pid=$process.Id; project=$projectRoot; service=$service; started_at=$process.StartTime.ToUniversalTime().ToString('o') } |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $serviceLogs "$name.pid.json") -Encoding utf8
        Write-ServiceLog "Started $service PID $($process.Id) at $($process.StartTime.ToUniversalTime().ToString('o'))"
    }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\health_check.ps1" -Target $Target -WaitReady -TimeoutSec $TimeoutSec
    if ($LASTEXITCODE -ne 0) { throw 'Health check failed. Inspect logs/backend.err.log and logs/frontend.err.log.' }
    foreach ($service in $services) {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort (Get-ServicePort $service) -ErrorAction SilentlyContinue)
        if (-not $listeners -or @($listeners | Where-Object { -not (Test-OwnedListener $_ $service) }).Count) {
            throw "$service health response came from an unowned process."
        }
    }
    Write-ServiceLog "Health and ownership verified for $Target"
    if ($OpenBrowser) { Start-Process 'http://127.0.0.1:3000' }
    exit 0
} catch {
    Write-ServiceLog "Startup failed: $($_.Exception.Message)"
    Write-Error $_.Exception.Message -ErrorAction Continue
    exit 1
}
