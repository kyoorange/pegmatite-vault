# 画面設計

実装時に参照する画面仕様の索引。

## 共通仕様

- [画面遷移とルーティング](./navigation.md)
- [共通レイアウト](./common-layout.md)

## ワイヤーフレーム

| 画面 | パス | 仕様 |
| --- | --- | --- |
| HOME | `/` | [HOME](./wireframes/home.md) |
| VAULT | `/vault` | [VAULT](./wireframes/vault.md) |
| 標本詳細 | `/specimens/:id` | [標本詳細](./wireframes/specimen-detail.md) |
| 標本登録・編集 | `/specimens/new`、`/specimens/:id/edit` | [標本フォーム](./wireframes/specimen-form.md) |
| LIBRARY | `/library` | [LIBRARY](./wireframes/library.md) |
| 鉱物詳細 | `/minerals/:id` | [鉱物詳細](./wireframes/mineral-detail.md) |
| 採集地詳細 | `/localities/:id` | [採集地詳細](./wireframes/locality-detail.md) |
| ADMIN | `/admin` 以下 | [ADMIN](./wireframes/admin.md) |
| SETTING | `/settings` | [SETTING](./wireframes/settings.md) |

VAULTは所有標本、LIBRARYは鉱物種を扱う。各画面では読み込み中、空状態、APIエラー、削除確認、未保存変更を考慮する。
