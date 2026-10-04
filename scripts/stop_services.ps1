[CmdletBinding()]
param([ValidateSet('All','Frontend','Backend')][string]$Target='All', [switch]$Quiet)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\service_common.ps1"
$services = if ($Target -eq 'All') { @('Backend','Frontend') } else { @($Target) }
foreach ($service in $services) {
    $roots = Get-ProjectRoots $service
    foreach ($root in $roots) {
        # Recheck ownership immediately before termination, including process creation time.
        $current = Get-CimInstance Win32_Process -Filter "ProcessId=$($root.ProcessId)" -ErrorAction SilentlyContinue
        if ($current -and $current.CreationDate -eq $root.CreationDate -and (Test-ProjectProcess $current $service)) {
            & taskkill.exe /PID $root.ProcessId /T /F | Out-Null
            Write-ServiceLog "Stopped owned $service PID $($root.ProcessId)"
        }
    }
    $port = Get-ServicePort $service
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        $owned = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { Test-OwnedListener $_ $service })
        if (-not $owned) { break }
        Start-Sleep -Milliseconds 300
    }
    if ($owned) { throw "Owned $service listener did not stop." }
    $pidFile = Join-Path $serviceLogs "$($service.ToLower()).pid.json"
    if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile }
    if (-not $Quiet) { Write-Host "$service project processes stopped; unrelated processes preserved." }
}
