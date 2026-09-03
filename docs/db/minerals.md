### minerals（鉱物種）

| カラム名（論理名） | カラム名（物理名）        | type    | constraints  | 運用イメージ                |
| --------- | ---------------- | ------- | ------------ | --------------------- |
| 鉱物種ID     | id               | uuid    | PK           | 自動採番                  |
| 和名        | japanese_name    | varchar | NOT NULL     | 石英、黄鉄鉱など              |
| 英名        | english_name     | varchar |              | Quartz、Pyriteなど       |
| 化学組成      | formula          | varchar |              | SiO₂、FeS₂など           |
| 結晶系       | crystal_system   | varchar |              | 等軸晶系、六方晶系など           |
| 鉱物分類ID    | mineral_class_id | int     | FK, NULL | mineral_classes.idを参照。未設定可 |
| 特徴        | description      | text    |              | 鉱物種の一般的な説明            |
