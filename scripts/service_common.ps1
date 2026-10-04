$projectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$serviceLogs = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Path $serviceLogs -Force | Out-Null

function Get-ServicePort([string]$Service) {
    if ($Service -eq 'Backend') { return 8000 }
    return 3000
}

function Test-ProjectProcess($Process, [string]$Service) {
    if (-not $Process -or -not $Process.CommandLine) { return $false }
    if ($Service -eq 'Backend') {
        $python = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
        return ($Process.ExecutablePath -eq $python -and $Process.CommandLine -match 'uvicorn\s+app\.main:app')
    }
    $nextEntry = Join-Path $projectRoot 'frontend\node_modules\next\dist\bin\next'
    return ($Process.Name -eq 'node.exe' -and $Process.CommandLine.Contains($nextEntry) -and
        $Process.CommandLine -match '\s(dev|start)(\s|$)')
}

function Get-ProjectRoots([string]$Service) {
    @(Get-CimInstance Win32_Process | Where-Object { Test-ProjectProcess $_ $Service })
}

function Test-OwnedListener($Listener, [string]$Service) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($Listener.OwningProcess)" -ErrorAction SilentlyContinue
    for ($depth = 0; $process -and $depth -lt 8; $depth++) {
        if (Test-ProjectProcess $process $Service) { return $true }
        $ancestor = $process.ParentProcessId
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ancestor" -ErrorAction SilentlyContinue
    }
    return $false
}

function Write-ServiceLog([string]$Message) {
    Add-Content -LiteralPath (Join-Path $serviceLogs 'services.log') -Value "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] $Message"
}
