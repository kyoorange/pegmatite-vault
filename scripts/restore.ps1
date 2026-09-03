[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [switch]$ConfirmRestore,
    [string]$ImageStorageRoot = ""
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "リストアは既存DBを置き換えます。実行する場合は -ConfirmRestore を指定してください。"
}

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Read-DotEnv {
    param([string]$Path)
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -eq 2) {
            $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
        }
    }
    return $values
}

$EnvFile = Join-Path $ProjectRoot ".env"
$Config = Read-DotEnv -Path $EnvFile
if (-not $Config.POSTGRES_USER -or -not $Config.POSTGRES_DB) {
    throw ".env の POSTGRES_USER と POSTGRES_DB を設定してください。"
}

$BackupFile = (Resolve-Path -LiteralPath $BackupFile).Path
if ([System.IO.Path]::GetExtension($BackupFile) -ne ".zip") {
    throw "バックアップZIPを指定してください。"
}
if (-not $ImageStorageRoot) {
    $RuntimeSettingsFile = if ($Config.RUNTIME_SETTINGS_FILE) {
        $Config.RUNTIME_SETTINGS_FILE
    } else {
        "./storage/runtime-settings.json"
    }
    if (-not [System.IO.Path]::IsPathRooted($RuntimeSettingsFile)) {
        $RuntimeSettingsFile = Join-Path $ProjectRoot $RuntimeSettingsFile
    }
    if (Test-Path -LiteralPath $RuntimeSettingsFile -PathType Leaf) {
        $RuntimeSettings = Get-Content -LiteralPath $RuntimeSettingsFile -Encoding UTF8 -Raw |
            ConvertFrom-Json
        $ImageStorageRoot = $RuntimeSettings.image_storage_root
    }
    if (-not $ImageStorageRoot) {
        $ImageStorageRoot = if ($Config.IMAGE_STORAGE_ROOT) {
            $Config.IMAGE_STORAGE_ROOT
        } else {
            "./storage"
        }
    }
}
if (-not [System.IO.Path]::IsPathRooted($ImageStorageRoot)) {
    $ImageStorageRoot = Join-Path $ProjectRoot $ImageStorageRoot
}
$ImageStorageRoot = [System.IO.Path]::GetFullPath($ImageStorageRoot)
$ImagesDirectory = Join-Path $ImageStorageRoot "images"

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RecoveryRoot = Join-Path $ProjectRoot "backups\pre-restore-$Timestamp"
$ExtractDirectory = Join-Path $RecoveryRoot "incoming"
$CurrentImagesBackup = Join-Path $RecoveryRoot "previous-images"
$PreRestoreDump = Join-Path $RecoveryRoot "previous-database.dump"
$ContainerIncoming = "/tmp/pegmatite-vault-restore-$Timestamp.dump"
$ContainerPrevious = "/tmp/pegmatite-vault-pre-restore-$Timestamp.dump"

New-Item -ItemType Directory -Path $ExtractDirectory -Force | Out-Null
try {
    Expand-Archive -LiteralPath $BackupFile -DestinationPath $ExtractDirectory
    $ManifestPath = Join-Path $ExtractDirectory "manifest.json"
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "manifest.json がありません。Pegmatite Vaultのバックアップではありません。"
    }
    $Manifest = Get-Content -LiteralPath $ManifestPath -Encoding UTF8 -Raw | ConvertFrom-Json
    if ($Manifest.format_version -ne 1) {
        throw "未対応のバックアップ形式です。"
    }
    $ExtractRootPrefix = $ExtractDirectory.TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    foreach ($entry in $Manifest.files) {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $ExtractDirectory $entry.path))
        if (-not $candidate.StartsWith($ExtractRootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "バックアップ内に不正なパスがあります。"
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "バックアップファイルが不足しています: $($entry.path)"
        }
        $actual = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $entry.sha256) {
            throw "チェックサムが一致しません: $($entry.path)"
        }
    }

    $IncomingDump = Join-Path $ExtractDirectory "database\pegmatite-vault.dump"
    $IncomingImages = Join-Path $ExtractDirectory "images"
    if (-not (Test-Path -LiteralPath $IncomingDump -PathType Leaf)) {
        throw "DBダンプがありません。"
    }
    if (-not (Test-Path -LiteralPath $IncomingImages -PathType Container)) {
        throw "画像ディレクトリがありません。"
    }

    Push-Location $ProjectRoot
    try {
        & docker compose exec -T db pg_dump `
            -U $Config.POSTGRES_USER `
            -d $Config.POSTGRES_DB `
            -Fc `
            -f $ContainerPrevious
        if ($LASTEXITCODE -ne 0) { throw "リストア前DBバックアップに失敗しました。" }
        & docker compose cp "db:$ContainerPrevious" $PreRestoreDump
        if ($LASTEXITCODE -ne 0) { throw "リストア前DBダンプのコピーに失敗しました。" }

        & docker compose cp $IncomingDump "db:$ContainerIncoming"
        if ($LASTEXITCODE -ne 0) { throw "リストア用DBダンプのコピーに失敗しました。" }
        & docker compose exec -T db pg_restore `
            -U $Config.POSTGRES_USER `
            -d $Config.POSTGRES_DB `
            --clean `
            --if-exists `
            --no-owner `
            $ContainerIncoming
        if ($LASTEXITCODE -ne 0) {
            throw "pg_restore に失敗しました。退避データ: $RecoveryRoot"
        }
    }
    finally {
        & docker compose exec -T db rm -f $ContainerIncoming $ContainerPrevious
        Pop-Location
    }

    if (Test-Path -LiteralPath $ImagesDirectory -PathType Container) {
        Move-Item -LiteralPath $ImagesDirectory -Destination $CurrentImagesBackup
    }
    New-Item -ItemType Directory -Path $ImageStorageRoot -Force | Out-Null
    Copy-Item -LiteralPath $IncomingImages -Destination $ImagesDirectory -Recurse

    Write-Host "Restore completed."
    Write-Host "Pre-restore recovery data: $RecoveryRoot"
    Write-Host "Run Alembic upgrade and verify the application before deleting recovery data."
}
catch {
    Write-Error $_
    Write-Host "Recovery data is preserved at: $RecoveryRoot"
    throw
}



