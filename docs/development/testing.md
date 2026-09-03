# テスト実行手順

## 通常テスト

### バックエンド

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
```

通常実行では、専用PostgreSQLを必要とする`integration`テストはスキップされる。

### フロントエンド

```powershell
cd frontend
npm run lint
npm test -- --run
npm run build
```

## PostgreSQL結合テスト

開発DBを使用せず、`compose.integration.yaml`で独立したPostgreSQL 17コンテナを起動する。

前提:

- Docker Desktopが起動している。
- `docker`コマンドへPATHが通っている。
- `backend/.venv`へ開発依存関係がインストールされている。
- ホストのTCPポート`55433`が空いている。

プロジェクトルートで実行する。

```powershell
.\scripts\test-integration.ps1
```

スクリプトは次を自動実行する。

1. tmpfsを使用したテスト専用PostgreSQLを起動する。
2. Alembic migrationを適用する。
3. `integration`マーカーのテストだけを実行する。
4. テスト画像を削除する。
5. テストDBコンテナと一時データを削除する。

現在の結合シナリオ:

1. 標本を登録する。
2. 標本を取得・更新する。
3. PNG画像をアップロードする。
4. WebPサムネイルを取得する。
5. 画像をアーカイブする。
6. アーカイブ一覧を確認する。
7. 画像を標本へ復元する。
8. 再アーカイブして完全削除する。
9. 標本を削除する。

テスト専用接続先:

```text
postgresql+psycopg://pegmatite_test:pegmatite_test@localhost:55433/pegmatite_vault_test
```

この認証情報はローカルの一時テストコンテナ専用で、通常DBには使用しない。

