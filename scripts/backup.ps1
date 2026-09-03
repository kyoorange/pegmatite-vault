[CmdletBinding()]
param(
    [string]$OutputDirectory = "backups",
    [string]$ImageStorageRoot = ""
)

$ErrorActionPreference = "Stop"
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
if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
    throw ".env が見つかりません: $EnvFile"
}
$Config = Read-DotEnv -Path $EnvFile
if (-not $Config.POSTGRES_USER -or -not $Config.POSTGRES_DB) {
    throw ".env の POSTGRES_USER と POSTGRES_DB を設定してください。"
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
if (-not (Test-Path -LiteralPath $ImagesDirectory -PathType Container)) {
    throw "画像ディレクトリが見つかりません: $ImagesDirectory"
}

if (-not [System.IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory = Join-Path $ProjectRoot $OutputDirectory
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BackupName = "pegmatite-vault-backup-$Timestamp"
$StagingDirectory = Join-Path $OutputDirectory ".$BackupName-staging"
$ArchivePath = Join-Path $OutputDirectory "$BackupName.zip"
$ContainerDump = "/tmp/$BackupName.dump"

if (Test-Path -LiteralPath $StagingDirectory) {
    throw "一時ディレクトリがすでに存在します: $StagingDirectory"
}
if (Test-Path -LiteralPath $ArchivePath) {
    throw "出力先がすでに存在します: $ArchivePath"
}

New-Item -ItemType Directory -Path $StagingDirectory | Out-Null
try {
    $DatabaseDirectory = Join-Path $StagingDirectory "database"
    $StagedImages = Join-Path $StagingDirectory "images"
    New-Item -ItemType Directory -Path $DatabaseDirectory | Out-Null

    Push-Location $ProjectRoot
    try {
        & docker compose exec -T db pg_dump `
            -U $Config.POSTGRES_USER `
            -d $Config.POSTGRES_DB `
            -Fc `
            -f $ContainerDump
        if ($LASTEXITCODE -ne 0) { throw "pg_dump に失敗しました。" }

        & docker compose cp "db:$ContainerDump" (Join-Path $DatabaseDirectory "pegmatite-vault.dump")
        if ($LASTEXITCODE -ne 0) { throw "DBダンプのコピーに失敗しました。" }

        & docker compose exec -T db rm -f $ContainerDump
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "コンテナ内の一時DBダンプを削除できませんでした: $ContainerDump"
        }
    }
    finally {
        Pop-Location
    }

    Copy-Item -LiteralPath $ImagesDirectory -Destination $StagedImages -Recurse

    $FileEntries = @()
    $StagingPrefixLength = $StagingDirectory.TrimEnd("\", "/").Length + 1
    foreach ($file in Get-ChildItem -LiteralPath $StagingDirectory -File -Recurse) {
        $relative = $file.FullName.Substring($StagingPrefixLength)
        $FileEntries += [ordered]@{
            path = $relative.Replace("\", "/")
            size = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    $Manifest = [ordered]@{
        format_version = 1
        created_at = (Get-Date).ToUniversalTime().ToString("o")
        postgres_database = $Config.POSTGRES_DB
        image_storage_source = $ImageStorageRoot
        files = $FileEntries
    }
    $Manifest | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $StagingDirectory "manifest.json") -Encoding UTF8

    Compress-Archive -Path (Join-Path $StagingDirectory "*") -DestinationPath $ArchivePath
    Write-Host "Backup completed: $ArchivePath"
}
finally {
    if (Test-Path -LiteralPath $StagingDirectory) {
        Remove-Item -LiteralPath $StagingDirectory -Recurse -Force
    }
}



