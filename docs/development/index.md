# 開発ドキュメント

| ドキュメント | 内容 |
| --- | --- |
| [ディレクトリ構成](./directory-structure.md) | 配置と責務 |
| [環境変数](./environment.md) | 設定値と管理方法 |
| [DB運用](./database-operations.md) | Docker、Alembic、初期データ、バックアップ |
| [CSV入出力 操作手順書](./csv-import-export-guide.md) | SETTINGからのCSV出力、事前検証、インポート |
| [バックアップ・リストア 操作手順書](./backup-restore-guide.md) | PostgreSQLと画像の一括保全・復旧 |
| [画像保存先変更 操作手順書](./image-storage-migration-guide.md) | 画像コピー、照合、保存先切り替え |
| [テスト実行手順](./testing.md) | 通常テストとPostgreSQL結合テスト |
| [コーディング規約](./coding-rules.md) | React、FastAPI、DB、テスト |
| [セットアップ](./setup.md) | 初回構築と日常の起動手順 |

仕様の優先順位は、OpenAPI、DB仕様、画面仕様、開発ドキュメント、実装の順とする。仕様間に矛盾がある場合は実装で吸収せず、先に該当ドキュメントを修正する。
