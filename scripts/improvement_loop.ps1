param(
    [string]$Config = "config\production_config.yaml",
    [string]$OutputRoot = "runs"
)

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $RepoRoot
try {
    python (Join-Path $PSScriptRoot "workflow_engine.py") improve --config $Config --output-root $OutputRoot
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
