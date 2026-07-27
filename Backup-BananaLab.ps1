#Requires -Version 5.1
<#
.SYNOPSIS
  Create a timestamped offline backup of MonkeyZoo production evidence.

.EXAMPLE
  .\Backup-BananaLab.ps1
  .\Backup-BananaLab.ps1 -Dest D:\Backups\MonkeyZoo -DryRun
#>
[CmdletBinding()]
param(
    [string]$Dest = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$pythonExe = $null
$pythonArgs = @()
$venv = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venv) {
    $pythonExe = $venv
} else {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $pythonExe = $cmd.Source
    } else {
        $pyCmd = Get-Command py -ErrorAction SilentlyContinue
        if ($pyCmd) {
            $pythonExe = "py"
            $pythonArgs = @("-3")
        }
    }
}
if (-not $pythonExe) {
    Write-Host "ERROR: Python not found. Run Start-BananaLab.ps1 first or install Python 3.10+." -ForegroundColor Red
    exit 1
}

$scriptPath = Join-Path $Root "scripts\backup_production.py"
$argsList = $pythonArgs + @($scriptPath)
if ($Dest) { $argsList += @("--dest", $Dest) }
if ($DryRun) { $argsList += "--dry-run" }

Write-Host "==> Banana Lab production backup" -ForegroundColor Cyan
& $pythonExe @argsList

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Backup finished." -ForegroundColor Green
