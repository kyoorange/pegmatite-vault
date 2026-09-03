# Pegmatite Vault

鉱物標本コレクションを登録、検索、閲覧、管理する個人用Webアプリケーション。

## 技術構成

| 領域 | 技術 |
| --- | --- |
| フロントエンド | React（JavaScript）＋ Vite |
| バックエンド | FastAPI |
| DB | PostgreSQL |
| ORM・マイグレーション | SQLAlchemy 2.x ＋ Alembic |
| 画像 | 指定したローカルディレクトリへ複製保存 |
| 認証 | なし |

※ 認証を実装しないため、個人PCまたは信頼できるLAN内での利用を前提とする。インターネットへ直接公開しない。

## ディレクトリ

```text
frontend/   Reactアプリケーション
backend/    FastAPI、SQLAlchemy、Alembic、テスト
storage/    アプリが管理する画像ファイル
docs/       実装時に参照する確定仕様
llm/        検討資料と実装計画
```

詳細は[ディレクトリ構成](./docs/development/directory-structure.md)を参照。

## ドキュメント

### 仕様

- [DB設計](./docs/db/0.index.md)
- [ER図](./docs/db/100.ER図.md)
- [API仕様](./docs/api/index.md)
- [OpenAPI 3.1定義](./docs/api/openapi.yaml)
- [画面設計](./docs/pages/index.md)
- [画面遷移](./docs/pages/navigation.md)

### 開発

- [開発ドキュメント索引](./docs/development/index.md)
- [環境変数](./docs/development/environment.md)
- [DB運用](./docs/development/database-operations.md)
- [CSV入出力 操作手順書](./docs/development/csv-import-export-guide.md)
- [バックアップ・リストア 操作手順書](./docs/development/backup-restore-guide.md)
- [画像保存先変更 操作手順書](./docs/development/image-storage-migration-guide.md)
- [テスト実行手順](./docs/development/testing.md)
- [コーディング規約](./docs/development/coding-rules.md)
- [セットアップ](./docs/development/setup.md)

### 計画

- [実装計画](./llm/実装計画.md)

## セットアップ概要

次の流れで開発環境を構築する。

1. `.env.example` を `.env` へコピーして設定する。
2. Docker ComposeでPostgreSQLを起動する。
3. バックエンド依存関係をインストールする。
4. Alembicでテーブルを作成する。
5. フロントエンド依存関係をインストールする。
6. FastAPIとViteを起動する。

```powershell
docker compose up -d db

cd backend
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

cd ..\frontend
npm run dev
```

完全な手順は[開発環境セットアップ](./docs/development/setup.md)を参照。

## DB作成

PostgreSQLコンテナの起動だけではアプリのテーブルは作成されない。DB起動後にAlembicを明示的に実行する。

```powershell
docker compose up -d db
cd backend
alembic upgrade head
```

## 画像管理

- アップロード元ファイルは変更せず、管理ディレクトリへ複製する。
- 1画像を1つのDBレコードとして管理する。
- オリジナル、表示用、サムネイルのパスは画像UUIDから導出する。
- 表示用とサムネイルはオリジナルから再生成できる。
- 標本削除時は画像を論理アーカイブし、通常の削除では物理ファイルを消さない。

詳細は[標本画像テーブル](./docs/db/images.md)を参照。

## 仕様変更

実装と仕様が異なる場合は実装だけを変更せず、対応する `docs/` を先に更新する。API契約はOpenAPI定義、DB構造はDB設計資料を正本とする。
