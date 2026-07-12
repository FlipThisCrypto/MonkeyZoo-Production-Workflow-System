param(
    [string]$Config = "config\production_config.yaml",
    [string]$OutputRoot = "runs"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Engine = Join-Path $PSScriptRoot "workflow_engine.py"

Push-Location $RepoRoot
try {
    python $Engine run --config $Config --output-root $OutputRoot
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
