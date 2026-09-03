### specimens（標本）

| カラム名（論理名） | カラム名（物理名）             | type      | constraints  | 運用イメージ                    |
| --------- | --------------------- | --------- | ------------ | ------------------------- |
| 標本ID      | id                    | uuid      | PK           | UUIDを自動採番                 |
| 標本No.     | specimen_no           | int       | NOT NULL, CHECK > 0 | 採集地ごとの通番。重複を許可          |
| 標本名       | specimen_name         | varchar   | NOT NULL     | 「曹長石を伴うリチア電気石」など          |
| 採集地ID     | locality_id           | uuid      | FK, NULL     | localities.idを参照。未設定可 |
| 入手経路ID    | acquisition_method_id | int       | FK, NULL | acquisition_methods.idを参照。未設定可 |
| 入手日       | collection_date       | date      |              | 採集日・購入日など                 |
| 特徴        | features              | text      |              | 肉眼的特徴など                   |
| 備考        | note                  | text      |              | 自由記述                      |
| お気に入り     | favorite              | boolean   | NOT NULL, DEFAULT false | トップ画面表示対象 |
| 登録日時      | created_at            | timestamptz | NOT NULL, DEFAULT now() | UTCで保存 |
| 更新日時      | updated_at            | timestamptz | NOT NULL, DEFAULT now() | UTCで保存。更新時にアプリが更新 |

## 標本番号の採番

- `(locality_id, specimen_no)` を含め、一意制約は設けない。
- 新規登録時に番号が未指定なら、APIが同じ `locality_id` の最大値へ1を加えて設定する。
- `locality_id` がNULLの場合は、採集地未設定の標本を対象に採番する。
- 対象レコードがなければ1から開始する。
- 番号が指定された場合はその値を使用し、重複も許容する。
- 同時登録による重複は許容し、DBシーケンスによる厳密な連番管理は行わない。

## 日時

日時はPostgreSQLの `timestamp with time zone`（`timestamptz`）でUTC保存する。画面表示時にブラウザのローカル時刻へ変換する。
