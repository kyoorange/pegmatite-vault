# 制約とインデックス

## 外部キー

| 親テーブル               | 子テーブル             | FK                                                       | ON DELETE | ON UPDATE |
| ------------------- | ----------------- | -------------------------------------------------------- | --------- | --------- |
| specimens           | images            | images.specimen_id → specimens.id                        | SET NULL  | CASCADE   |
| specimens           | specimen_minerals | specimen_minerals.specimen_id → specimens.id             | CASCADE   | CASCADE   |
| minerals            | specimen_minerals | specimen_minerals.mineral_id → minerals.id               | RESTRICT  | CASCADE   |
| localities          | specimens         | specimens.locality_id → localities.id                    | RESTRICT  | CASCADE   |
| acquisition_methods | specimens         | specimens.acquisition_method_id → acquisition_methods.id | RESTRICT  | CASCADE   |
| mineral_classes     | minerals          | minerals.mineral_class_id → mineral_classes.id           | RESTRICT  | CASCADE   |

標本削除APIはトランザクション内で関連画像を先に `archived` に更新してから標本を削除する。active画像を残したまま標本だけを直接削除すると、`ON DELETE SET NULL` と画像状態のCHECK制約が両立しないため、DBが削除を拒否する。

## CHECK制約

| テーブル | 制約 |
| --- | --- |
| specimens | `specimen_no > 0` |
| images | `file_size >= 0` |
| images | `sort_order >= 0` |
| images | `status IN ('active', 'archived')` |
| images | active時は `specimen_id IS NOT NULL AND archived_from_specimen_id IS NULL AND archived_at IS NULL` |
| images | archived時は `specimen_id IS NULL AND archived_from_specimen_id IS NOT NULL AND archived_at IS NOT NULL` |
| localities | `latitude BETWEEN -90 AND 90` |
| localities | `longitude BETWEEN -180 AND 180` |

## 一意制約

- `specimen_minerals`: `(specimen_id, mineral_id)` を複合主キーとする。
- `mineral_classes.name` と `acquisition_methods.name` は一意とする。
- `specimens.specimen_no` は採集地との組み合わせを含め、一意制約を設けない。
- `images.sort_order` は編集中の並べ替えを容易にするため、一意制約を設けない。

## 初期インデックス

| テーブル | カラム | 目的 |
| --- | --- | --- |
| specimens | `locality_id` | 採集地による絞り込みとAPI採番 |
| specimens | `acquisition_method_id` | 入手経路による絞り込み |
| specimens | `created_at` | 最近追加した標本 |
| specimens | `favorite` | お気に入り一覧 |
| specimen_minerals | `mineral_id` | 鉱物から関連標本を取得 |
| minerals | `mineral_class_id` | 鉱物分類による絞り込み |
| images | `(specimen_id, sort_order)` | active画像の表示順取得 |
| images | `(status, archived_at)` | アーカイブ画像の管理 |
