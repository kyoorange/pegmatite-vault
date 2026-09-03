# 環境変数

ルートの `.env` をDocker Composeとローカル開発で使用する。秘密情報や環境固有値をコミットせず、キーと安全な例だけを `.env.example` に記載する。

## 設定一覧

| 変数 | 必須 | 例 | 用途 |
| --- | --- | --- | --- |
| `POSTGRES_DB` | Yes | `pegmatite_vault` | DB名 |
| `POSTGRES_USER` | Yes | `pegmatite` | DBユーザー |
| `POSTGRES_PASSWORD` | Yes | `change-me` | DBパスワード |
| `POSTGRES_HOST` | Yes | `localhost` | FastAPIから見たDBホスト |
| `POSTGRES_PORT` | Yes | `5433` | DBポート |
| `DATABASE_URL` | Yes | `postgresql+psycopg://...` | SQLAlchemy接続URL |
| `IMAGE_STORAGE_ROOT` | Yes | `./storage` | 画像管理領域のルート |
| `RUNTIME_SETTINGS_FILE` | No | `./storage/runtime-settings.json` | SETTING画面で変更した保存先の永続化ファイル |
| `IMAGE_MAX_UPLOAD_BYTES` | No | `20971520` | 1ファイルの上限。既定20 MiB |
| `IMAGE_DISPLAY_MAX_PX` | No | `1920` | 表示用画像の長辺上限 |
| `IMAGE_THUMBNAIL_MAX_PX` | No | `480` | サムネイルの長辺上限 |
| `CORS_ORIGINS` | Yes | `http://localhost:5173,http://127.0.0.1:5173` | 許可するフロントエンドOrigin |
| `LOG_LEVEL` | No | `INFO` | バックエンドのログレベル |
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000/api` | フロントエンドのAPI URL |

## 運用規則

- `DATABASE_URL` と個別のPostgreSQL変数が競合しないよう、アプリは `DATABASE_URL` を接続情報の正本とする。
- Docker Composeは個別変数からPostgreSQLコンテナを構成する。
- Windowsの絶対パスを `.env` に書く場合は、アプリ側で正規化して利用する。
- `IMAGE_STORAGE_ROOT` は起動時に存在、書き込み権限、空き容量を確認する。
- CORSは完全一致で許可し、認証なしであるため `*` を指定しない。
- `VITE_` で始まる値はブラウザへ公開される。秘密情報を設定しない。
- `.env.example` のパスワードは開発用の例であり、実環境では変更する。

## 設定の読み込み

- FastAPIはPydantic Settingsで読み込み、起動時に検証する。
- 必須値の欠落や不正な値がある場合は、曖昧な既定値で起動せずエラー終了する。
- 画像保存先をSETTING画面から変更した場合、`RUNTIME_SETTINGS_FILE`に保存された絶対パスが`IMAGE_STORAGE_ROOT`より優先される。
