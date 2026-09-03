[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendRoot = Join-Path $ProjectRoot "backend"
$ComposeFile = Join-Path $ProjectRoot "compose.integration.yaml"
$TestStorage = Join-Path $ProjectRoot "storage\integration-test"
$TestDatabaseUrl = "postgresql+psycopg://pegmatite_test:pegmatite_test@localhost:55433/pegmatite_vault_test"

if (-not $TestStorage.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "テスト画像ディレクトリがプロジェクト外です。"
}

$PreviousDatabaseUrl = $env:DATABASE_URL
$PreviousTestDatabaseUrl = $env:TEST_DATABASE_URL
$PreviousImageStorageRoot = $env:IMAGE_STORAGE_ROOT

try {
    Push-Location $ProjectRoot
    & docker compose -f $ComposeFile up -d --wait db-test
    if ($LASTEXITCODE -ne 0) { throw "テスト用PostgreSQLを起動できませんでした。" }

    $env:DATABASE_URL = $TestDatabaseUrl
    $env:TEST_DATABASE_URL = $TestDatabaseUrl
    $env:IMAGE_STORAGE_ROOT = $TestStorage

    Push-Location $BackendRoot
    try {
        & .\.venv\Scripts\python.exe -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "テストDBのmigrationに失敗しました。" }
        & .\.venv\Scripts\python.exe -m pytest -m integration
        if ($LASTEXITCODE -ne 0) { throw "結合テストに失敗しました。" }
    }
    finally {
        Pop-Location
    }
}
finally {
    $env:DATABASE_URL = $PreviousDatabaseUrl
    $env:TEST_DATABASE_URL = $PreviousTestDatabaseUrl
    $env:IMAGE_STORAGE_ROOT = $PreviousImageStorageRoot
    if (Test-Path -LiteralPath $TestStorage) {
        $ResolvedTestStorage = (Resolve-Path -LiteralPath $TestStorage).Path
        if ($ResolvedTestStorage.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $ResolvedTestStorage -Recurse -Force
        }
    }
    Pop-Location
    & docker compose -f $ComposeFile down --volumes
}

