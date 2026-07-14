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

$python = $null
$venv = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $venv) {
    $python = $venv
} else {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python) {
    Write-Host "ERROR: Python not found. Run Start-BananaLab.ps1 first or install Python 3.10+." -ForegroundColor Red
    exit 1
}

$argsList = @("scripts\backup_production.py")
if ($Dest) { $argsList += @("--dest", $Dest) }
if ($DryRun) { $argsList += "--dry-run" }

Write-Host "==> Banana Lab production backup" -ForegroundColor Cyan
& $python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Backup finished." -ForegroundColor Green
