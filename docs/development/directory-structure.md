# ディレクトリ構成

```text
pegmatite-vault/
├── frontend/
│   ├── public/
│   └── src/
│       ├── api/
│       ├── assets/
│       ├── components/
│       ├── features/
│       │   ├── admin/
│       │   ├── localities/
│       │   ├── minerals/
│       │   └── specimens/
│       ├── layouts/
│       ├── pages/
│       ├── routes/
│       └── styles/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   └── tests/
├── storage/
│   └── images/
├── docs/
│   ├── api/
│   ├── db/
│   ├── development/
│   └── pages/
├── llm/
├── compose.yaml
├── .env
├── .env.example
└── README.md
```

## フロントエンド

- `api/`: HTTPクライアント、APIごとの呼び出し関数。コンポーネントに直接 `fetch` を散在させない。
- `assets/`: アプリに同梱する静的素材。登録画像は置かない。
- `components/`: 複数機能で共有する表示部品。
- `features/`: ドメイン単位の部品、hooks、画面固有ロジック。
- `layouts/`: ヘッダー、サイドメニュー、共通ページ枠。
- `pages/`: ルートに対応するページコンポーネント。業務ロジックを集中させない。
- `routes/`: React Routerの定義と404処理。
- `styles/`: 共通スタイル、変数、リセット。

機能内だけで利用するものは `features/<feature>/` に置き、2機能以上で共用するときだけ上位へ移動する。

## バックエンド

- `api/routes/`: HTTP入出力、依存注入、ステータスコード。業務処理を実装しない。
- `core/`: 環境設定、ログ、例外、セキュリティ関連の共通処理。
- `db/`: Engine、Session、Base、トランザクション補助。
- `models/`: SQLAlchemyモデル。
- `schemas/`: PydanticのAPI入出力モデル。
- `repositories/`: DBアクセスとクエリ。
- `services/`: 採番、関連更新、画像処理などの業務処理。
- `alembic/versions/`: DB変更履歴。適用済みファイルを書き換えず、新しいrevisionを追加する。
- `tests/`: API、サービス、DB制約のテスト。

依存方向は `routes → services → repositories → db/models` とする。下位層から上位層を参照しない。

## ストレージ

```text
storage/images/<image UUID>/
├── original.<ext>
├── display.webp
└── thumbnail.webp
```

実画像はGit管理しない。パスは画像UUIDから導出し、DBへ派生画像ごとのパスを保存しない。

## ドキュメント

- `docs/`: 実装時に参照する確定仕様。
- `llm/`: 検討資料、計画、作業支援用資料。

確定した内容は `llm/` だけに残さず、該当する `docs/` の仕様へ反映する。
