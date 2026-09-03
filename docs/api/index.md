# API仕様

API仕様の正本は [OpenAPI 3.1定義](./openapi.yaml) とする。FastAPI実装、フロントエンドのAPIクライアント、テストはこの定義と一致させる。

## 基本方針

- ベースパス: `/api`
- データ形式: JSON
- JSONフィールド名: `snake_case`
- ID: UUID文字列。整数マスタのみ正の整数
- 日時: ISO 8601形式。DBではUTC保存し、レスポンスはUTCオフセット付きで返す
- 日付: `YYYY-MM-DD`
- 画像アップロード: `multipart/form-data`
- 認証: なし

## 共通レスポンス

- 一覧は `items`、`page`、`page_size`、`total` を返す。
- 入力不正は `422`、存在しないリソースは `404` を返す。
- 使用中マスタの削除など、現在状態と競合する操作は `409` を返す。
- 画像サイズ超過は `413`、未対応形式は `415` を返す。
- エラー本文は `error.code`、`error.message`、必要に応じて `error.details` を含む。

## セキュリティヘッダー

全APIレスポンスへ次を付与する。

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

## 画像配信

画像ファイルの物理パスはAPI利用者へ公開しない。画像IDとvariantを指定して取得する。

```text
GET /api/images/{image_id}/content?variant=thumbnail
GET /api/images/{image_id}/content?variant=display
GET /api/images/{image_id}/content?variant=original
```

`display` と `thumbnail` が存在しない場合、バックエンドがオリジナルから再生成する。

## 変更手順

1. API変更時は先に `openapi.yaml` を更新する。
2. DB制約や画面動作へ影響する場合は関連ドキュメントも更新する。
3. OpenAPIの構文検証後に実装とテストを変更する。

`backend/tests/test_openapi_contract.py`は、FastAPIが生成する全パス、HTTPメソッド、`operationId`がこのOpenAPI定義と一致することを検査する。
