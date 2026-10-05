[CmdletBinding()]
param([ValidateSet('All','Frontend','Backend')][string]$Target='All', [switch]$RestartOld=$true,
      [switch]$OpenBrowser=$false, [int]$TimeoutSec=60)
$ErrorActionPreference='Stop'
. "$PSScriptRoot\service_common.ps1"
$services = if ($Target -eq 'All') { @('Backend','Frontend') } else { @($Target) }
try {
    # Phase 4: Pre-Start Restore Manifest Guard
    $backendDir = Join-Path $projectRoot 'backend'
    $pythonExe = Join-Path $backendDir '.venv\Scripts\python.exe'
    if (Test-Path $pythonExe) {
        $prevPythonPath = $env:PYTHONPATH
        $env:PYTHONPATH = "$backendDir;$env:PYTHONPATH"
        $guardCheck = & $pythonExe -m app.commands.restore_helper check-guard 2>&1
        $guardExit = $LASTEXITCODE
        $env:PYTHONPATH = $prevPythonPath
        if ($guardExit -ne 0) {
            Write-Host $guardCheck -ForegroundColor Red
            throw "Khởi động dịch vụ bị CHẶN bởi restore manifest guard. Chạy 'RESTORE.bat --recover' để xử lý."
        }
    }

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
        $outLog = Join-Path $serviceLogs "$name.out.log"
        $errLog = Join-Path $serviceLogs "$name.err.log"
        if ($service -eq 'Backend') {
            $cmdLine = "cmd.exe /d /c `"`"$executable`" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > `"$outLog`" 2> `"$errLog`"`""
        } else {
            $cmdLine = "cmd.exe /d /c `"set NEXT_DIST_DIR=.next-dev&& `"$executable`" `"$entry`" dev --hostname 127.0.0.1 --port 3000 > `"$outLog`" 2> `"$errLog`"`""
        }
        $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
            CommandLine = $cmdLine
            CurrentDirectory = $workingDir
        }
        if ($r.ReturnValue -ne 0) {
            throw "Failed to start $service via WMI (error code $($r.ReturnValue))"
        }
        $startTime = (Get-Date).ToUniversalTime().ToString('o')
        @{ pid=$r.ProcessId; project=$projectRoot; service=$service; started_at=$startTime } |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $serviceLogs "$name.pid.json") -Encoding utf8
        Write-ServiceLog "Started $service PID $($r.ProcessId) at $startTime"
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
