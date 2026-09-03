# バックアップ・リストア 操作手順書

## 1. 概要

Pegmatite Vaultの完全なバックアップは、PostgreSQLのDBダンプと画像ストレージを同じ時点の一組として保存する。

CSV入出力は画像ファイル本体を扱わないため、障害復旧やPC移行にはこの手順を使用する。

## 2. バックアップに含まれるもの

- PostgreSQLカスタム形式ダンプ
- オリジナル画像
- 表示用画像
- サムネイル
- ファイルサイズとSHA-256チェックサムを記録した`manifest.json`

## 3. バックアップ前の準備

1. Docker Desktopを起動する。
2. PostgreSQLコンテナがhealthyであることを確認する。
3. FastAPIを停止し、バックアップ中にデータが更新されないようにする。
4. PowerShellでプロジェクトルートを開く。

```powershell
docker compose ps
```

## 4. バックアップ

プロジェクトルートで次を実行する。

```powershell
.\scripts\backup.ps1
```

正常終了すると`backups/`に次のZIPが作成される。

```text
backups/pegmatite-vault-backup-YYYYMMDDTHHMMSSZ.zip
```

出力先を変更する場合:

```powershell
.\scripts\backup.ps1 -OutputDirectory "D:\PegmatiteBackups"
```

画像保存先を一時的に明示する場合:

```powershell
.\scripts\backup.ps1 -ImageStorageRoot "D:\PegmatiteImages"
```

### バックアップ後の確認

1. ZIPファイルが作成されている。
2. ZIPサイズが0バイトではない。
3. ZIP内に`manifest.json`、`database/pegmatite-vault.dump`、`images/`がある。
4. ZIPを別ドライブまたは外部媒体へ複製する。

## 5. リストア前の注意

リストアは現在のDB内容を置き換える破壊的操作である。

- FastAPIを停止する。
- 対象ZIPが正しい世代か確認する。
- PostgreSQLコンテナを起動する。
- 十分な空き容量を確保する。
- 処理中にPowerShellやDocker Desktopを終了しない。

リストアスクリプトは実行直前のDBと画像を`backups/pre-restore-<日時>/`へ自動退避する。この退避データは動作確認が終わるまで削除しない。

## 6. リストア

`-ConfirmRestore`を付けなければ実行されない。

```powershell
.\scripts\restore.ps1 `
  -BackupFile ".\backups\pegmatite-vault-backup-YYYYMMDDTHHMMSSZ.zip" `
  -ConfirmRestore
```

画像保存先を明示する場合:

```powershell
.\scripts\restore.ps1 `
  -BackupFile "D:\PegmatiteBackups\pegmatite-vault-backup-YYYYMMDDTHHMMSSZ.zip" `
  -ImageStorageRoot "D:\PegmatiteImages" `
  -ConfirmRestore
```

スクリプトは次の順序で処理する。

1. ZIPを展開する。
2. `manifest.json`を確認する。
3. 全ファイルのSHA-256を照合する。
4. 現在のDBを退避する。
5. PostgreSQLダンプを復元する。
6. 現在の画像を退避する。
7. 対応する画像ディレクトリを配置する。

## 7. リストア後の確認

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

その後、FastAPIとフロントエンドを起動し、次を確認する。

1. `SETTING`でDBと画像ストレージが正常。
2. `VAULT`の標本件数が想定どおり。
3. 複数の標本詳細を開ける。
4. オリジナル画像・表示画像・サムネイルを表示できる。
5. `LIBRARY`と`ADMIN`のマスタ件数が想定どおり。

問題がなければ、退避データの保管期限を決める。確認直後に削除しない。

## 8. 失敗時

- スクリプトが示した`backups/pre-restore-<日時>/`を削除しない。
- 再実行を繰り返さず、エラーメッセージとDockerログを保存する。
- DB復元前に失敗した場合、現DBは変更されていない。
- DB復元後に画像配置で失敗した場合、退避された`previous-images`を使用して元へ戻せる。
- `previous-database.dump`はリストア直前のDBである。

```powershell
docker compose logs db
```

## 9. 保管方針

- 最低でも複数世代を保持する。
- PC本体とは別の媒体にも保存する。
- ZIPを編集・再圧縮しない。
- パスワードや`.env`はバックアップZIPに含まれないため、別途安全に管理する。
- 定期的に検証用環境でリストア手順を確認する。
