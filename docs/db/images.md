# images（標本画像）

1レコードを1つの画像資産として扱う。オリジナル、表示用、サムネイルの各パスはDBへ保存せず、画像IDと固定ファイル名から導出する。

| カラム名（論理名） | カラム名（物理名） | type | constraints | 運用イメージ |
| --- | --- | --- | --- | --- |
| 画像ID | id | uuid | PK | UUIDを自動採番。保存ディレクトリ名にも使用 |
| 標本ID | specimen_id | uuid | FK, NULL | active時の関連標本。アーカイブ時はNULL |
| アーカイブ元標本ID | archived_from_specimen_id | uuid | NULL | 削除前に関連していた標本ID。FKは設定しない |
| 元ファイル名 | original_filename | varchar | NOT NULL | 利用者が選択したファイルの表示・記録用名称 |
| 元拡張子 | original_extension | varchar | NOT NULL | `jpg`、`jpeg`、`png`、`webp` |
| メディアタイプ | media_type | varchar | NOT NULL | 検査後のMIMEタイプ |
| ファイルサイズ | file_size | bigint | NOT NULL, CHECK >= 0 | オリジナル複製のバイト数 |
| キャプション | caption | varchar | NULL | 「正面」「劈開面」など |
| 表示順 | sort_order | int | NOT NULL, DEFAULT 0, CHECK >= 0 | 同一標本内の表示順 |
| 状態 | status | varchar | NOT NULL, DEFAULT 'active' | `active` または `archived` |
| アーカイブ日時 | archived_at | timestamptz | NULL | UTCで保存 |
| 登録日時 | created_at | timestamptz | NOT NULL, DEFAULT now() | UTCで保存 |

## ファイル配置

```text
<IMAGE_STORAGE_ROOT>/images/<images.id>/
├── original.<original_extension>
├── display.webp
└── thumbnail.webp
```

- `file_path`、`display_path`、`thumbnail_path` は保持しない。
- オリジナルは恒久データ、表示用画像とサムネイルは再生成可能な派生データとする。
- 保存先ルートを変更してもDBレコードは更新しない。

## 状態遷移

```text
active
  ├─ 標本削除 → archived
  └─ 画像削除 → archived

archived
  ├─ 標本へ再関連付け → active
  └─ 完全削除 → DBレコードとファイルを削除
```

- active時は `specimen_id` を必須とし、`archived_from_specimen_id` と `archived_at` はNULLとする。
- archived時は `specimen_id` をNULLにし、`archived_from_specimen_id` と `archived_at` を設定する。
- 論理アーカイブでは画像ファイルを移動・削除しない。
- 復元時は新しい `specimen_id` を設定し、アーカイブ関連項目をNULLへ戻す。
