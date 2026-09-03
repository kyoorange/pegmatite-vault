# 開発環境セットアップ

この手順をPhase 0以降の標準手順とする。スクリプト名は `package.json` と `pyproject.toml` を正本とし、差異が生じた場合は本書も更新する。

## 前提

- Git
- Node.js LTS
- Python 3.12以降
- Docker DesktopとDocker Compose

## 初回セットアップ

1. `.env.example` を `.env` へコピーし、パスワードと画像保存先を設定する。
2. PostgreSQLを起動する。

```powershell
docker compose up -d db
docker compose ps
```

3. バックエンド依存関係をインストールする。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

4. DBを構築する。

```powershell
alembic upgrade head
python -m app.db.seed
```

5. フロントエンド依存関係をインストールする。

```powershell
cd ..\frontend
npm install
```

## 開発サーバー

バックエンド:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

フロントエンド:

```powershell
cd frontend
npm run dev
```

想定URL:

- フロントエンド: `http://localhost:5173`
- API: `http://localhost:8000/api`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## 品質確認

バックエンド:

```powershell
cd backend
ruff check .
ruff format --check .
pytest
```

フロントエンド:

```powershell
cd frontend
npm run lint
npm run format:check
npm test
```

E2E:

```powershell
cd frontend
npm run test:e2e
```

## 終了

開発サーバーを停止した後、DBコンテナを停止する。

```powershell
docker compose stop db
```

DBデータも削除する操作は通常の終了手順に含めない。

## トラブルシューティング

- DB接続失敗: `docker compose ps`、`.env`、ポート競合、コンテナログを確認する。
- CORSエラー: ブラウザのOriginと `CORS_ORIGINS` の完全一致を確認する。
- 画像保存失敗: `IMAGE_STORAGE_ROOT` の存在、書き込み権限、空き容量を確認する。
- マイグレーション不一致: `alembic current` と `alembic heads` を比較する。
