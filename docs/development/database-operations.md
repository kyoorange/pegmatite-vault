# DB運用

## 基本方針

PostgreSQLはDocker Composeで起動する。コンテナ起動はDBサーバーを利用可能にするだけで、アプリのテーブルは作成しない。テーブル、制約、インデックスはAlembicで管理する。

```text
PostgreSQLコンテナ起動
  ↓
ヘルスチェック成功
  ↓
Alembic upgrade
  ↓
初期マスタ投入
  ↓
FastAPI起動
```

## 初回構築

```powershell
docker compose up -d db
cd backend
alembic upgrade head
```

その後、seedコマンドで入手経路、鉱物分類、基本的な鉱物の初期マスタを投入する。seedは再実行可能で、既存レコードを重複登録しない。既存レコードの内容は上書きしない。

```powershell
python -m app.db.seed
```

## CSVエクスポート

SETTING画面の「CSV出力」は、次のUTF-8 BOM付きCSVをZIP形式で出力する。

- `mineral_classes.csv`
- `minerals.csv`
- `localities.csv`
- `acquisition_methods.csv`
- `specimens.csv`
- `specimen_minerals.csv`
- `images.csv`

UUIDと外部キーを含むためテーブル間の対応を確認できる。画像ファイル本体は含まれないため、バックアップ用途では画像ストレージも必ず同時に保存する。

## CSVインポート

SETTING画面からエクスポートZIPを選択すると、ファイル構成、CSVヘッダー、ID形式、重複ID、外部キー参照を事前検証する。検証結果には追加・更新・スキップ件数と問題箇所を表示し、利用者が確定した場合だけ反映する。

- 既存データは削除しない。
- 同じIDのレコードは更新し、存在しないIDは追加する。
- 全テーブルを1トランザクションで更新し、途中で失敗した場合は全変更をロールバックする。
- 検証トークンの有効期限は30分で、一度確定すると再利用できない。
- `images.csv` は画像ファイル本体を含まないため、インポート対象外としてスキップする。
- 画像を含む環境復元にはCSVではなく、PostgreSQLと画像ストレージを一組にしたバックアップを使用する。

## 日常操作

```powershell
docker compose up -d db
docker compose ps
docker compose logs db
docker compose stop db
```

## マイグレーション作成

```powershell
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

自動生成結果をそのまま適用せず、次をレビューする。

- 型、NULL、DEFAULT
- 外部キーの `ON DELETE` と `ON UPDATE`
- CHECK・一意制約
- インデックス
- downgradeの安全性
- データ移行が必要なカラム変更

適用済みrevisionを編集しない。変更が必要なら新しいrevisionを作成する。

## ロールバック

```powershell
alembic downgrade -1
```

本番相当データでは、実行前にバックアップを取得する。カラム削除などデータを失うdowngradeは、復元手順を確認してから実行する。

## テストDB

- PostgreSQL専用型や制約差を見落とさないため、SQLiteで代用しない。
- 開発DBと異なるDB名を使用する。
- テスト実行単位でトランザクションを分離する。
- 並列実行時はDBまたはschemaを分離する。

## バックアップ

DBと画像ストレージを同一時点の一組として扱う。

FastAPIを停止してから、プロジェクトルートでバックアップスクリプトを実行する。

```powershell
.\scripts\backup.ps1
```

PostgreSQLダンプ、`IMAGE_STORAGE_ROOT/images/`、SHA-256チェックサム付きmanifestを1つのZIPへ保存する。表示用・サムネイルは再生成可能だが、通常のバックアップでは画像ディレクトリ全体を保存する。

## リストア

FastAPIを停止し、明示的な確認フラグを付けて実行する。

```powershell
.\scripts\restore.ps1 -BackupFile "<backup.zip>" -ConfirmRestore
```

リストア前のDBと画像は`backups/pre-restore-<日時>/`へ自動退避する。復元後はAlembicを最新状態へ更新し、DB、画像、主要画面を確認する。詳細は[バックアップ・リストア 操作手順書](./backup-restore-guide.md)を参照する。
