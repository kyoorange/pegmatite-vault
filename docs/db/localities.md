### localities（採集地）

| カラム名（論理名） | カラム名（物理名）     | type          | constraints | 運用イメージ           |
| --------- | ------------- | ------------- | ----------- | ---------------- |
| 採集地ID     | id            | uuid          | PK          | UUIDを自動採番        |
| 地名        | locality_name | varchar       | NOT NULL    | 長崎県西海市雪浦町など      |
| 通称        | alias_name    | varchar       |             | 雪浦川、○○露頭など       |
| 緯度        | latitude      | decimal(10,7) |             | OpenStreetMap表示用 |
| 経度        | longitude     | decimal(10,7) |             | OpenStreetMap表示用 |
| 備考        | note          | text          |             | アクセス方法や地質など      |
