#Requires -Version 5.1
<#
.SYNOPSIS
  One-command local startup for The Banana Lab (MonkeyZoo Studio).

.DESCRIPTION
  Locates Python, creates/uses .venv when present, installs missing core deps,
  launches the local writable review app, and prints the URL.

.EXAMPLE
  .\Start-BananaLab.ps1
#>
[CmdletBinding()]
param(
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Fail([string]$Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Find-Python {
    $candidates = @()
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { $candidates += $venvPython }

    foreach ($name in @("py", "python", "python3")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
    }

    foreach ($candidate in $candidates) {
        try {
            if ($candidate -eq "py" -or (Split-Path -Leaf $candidate) -eq "py.exe") {
                $version = & py -3 -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
                if ($LASTEXITCODE -eq 0 -and $version) {
                    return @{ Exe = "py"; Args = @("-3"); Version = $version }
                }
            } else {
                $version = & $candidate -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>$null
                if ($LASTEXITCODE -eq 0 -and $version) {
                    return @{ Exe = $candidate; Args = @(); Version = $version }
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

function Ensure-Venv([hashtable]$Python) {
    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        Write-Step "Using existing virtualenv: .venv"
        return $venvPython
    }

    Write-Step "Creating virtualenv at .venv"
    if ($Python.Exe -eq "py") {
        & py -3 -m venv (Join-Path $Root ".venv")
    } else {
        & $Python.Exe -m venv (Join-Path $Root ".venv")
    }
    if (-not (Test-Path $venvPython)) {
        throw "Virtualenv creation failed. Install Python 3.10+ and retry."
    }
    return $venvPython
}

function Ensure-Dependencies([string]$PythonExe) {
    Write-Step "Checking Python dependencies (flask, pillow, pyyaml, jsonschema)"
    $code = @'
import importlib.util, sys
missing = [n for n in ("flask", "PIL", "yaml", "jsonschema") if importlib.util.find_spec(n) is None]
if missing:
    print(",".join(missing))
    sys.exit(2)
print("ok")
'@
    $probe = & $PythonExe -c $code
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Dependencies present"
        return
    }

    Write-Step "Installing missing packages: $probe"
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install flask pillow pyyaml jsonschema
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed. Fix network/permissions, then re-run Start-BananaLab.ps1"
    }
}

function Test-PortFree([int]$PortNumber) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $PortNumber)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

try {
    Write-Host ""
    Write-Host "The Banana Lab by Fiend Studios — MonkeyZoo local runtime" -ForegroundColor Yellow
    Write-Host "Workspace: $Root"
    Write-Host ""

    $app = Join-Path $Root "character-bibles\_review_app\app.py"
    if (-not (Test-Path $app)) {
        throw "Missing app entrypoint: character-bibles\_review_app\app.py"
    }

    $python = Find-Python
    if (-not $python) {
        throw "Python 3 not found. Install Python 3.10+ from python.org and ensure it is on PATH."
    }
    Write-Step "Found Python $($python.Version) via $($python.Exe)"

    $pythonExe = Ensure-Venv $python
    Ensure-Dependencies $pythonExe

    if (-not (Test-PortFree $Port)) {
        throw "Port $Port is already in use. Stop the other process or re-run with -Port <free-port>."
    }

    $url = "http://127.0.0.1:$Port/"
    Write-Step "Launching MonkeyZoo Studio"
    Write-Host ""
    Write-Host "Open: $url" -ForegroundColor Green
    Write-Host "This is the local writable runtime. GitHub Pages remains read-only." -ForegroundColor DarkGray
    Write-Host "Press Ctrl+C to stop." -ForegroundColor DarkGray
    Write-Host ""

    if (-not $NoBrowser) {
        Start-Process $url | Out-Null
    }

    # app.py hardcodes 8765; warn if overridden without code change.
    if ($Port -ne 8765) {
        Write-Host "NOTE: app.py currently listens on 8765. -Port does not rebind the Flask app yet." -ForegroundColor Yellow
        Write-Host "Stopping with non-default port request to avoid a misleading launch." -ForegroundColor Yellow
        throw "Use default port 8765, or update character-bibles/_review_app/app.py to accept a port."
    }

    Set-Location (Join-Path $Root "character-bibles\_review_app")
    & $pythonExe "app.py"
} catch {
    Write-Fail $_.Exception.Message
    Write-Host ""
    Write-Host "Recovery tips:" -ForegroundColor Yellow
    Write-Host "  1. Install Python 3.10+ and re-open this shell"
    Write-Host "  2. From repo root: python -m venv .venv"
    Write-Host "  3. .\.venv\Scripts\python.exe -m pip install flask pillow pyyaml jsonschema"
    Write-Host "  4. .\.venv\Scripts\python.exe character-bibles\_review_app\app.py"
    Write-Host "  5. See docs/OPERATOR_RUNBOOK.md"
    exit 1
}
