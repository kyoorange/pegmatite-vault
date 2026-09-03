### specimen_minerals（標本-鉱物種）

| カラム名（論理名） | カラム名（物理名）   | type | constraints      | 運用イメージ          |
| --------- | ----------- | ---- | ---------------- | --------------- |
| 標本ID      | specimen_id | uuid | PK, FK, NOT NULL | specimens.idを参照 |
| 鉱物種ID     | mineral_id  | uuid | PK, FK, NOT NULL | minerals.idを参照  |
