### mineral_classes（鉱物分類）

| カラム名（論理名） | カラム名（物理名） | type | constraints | 運用イメージ |
|-------------------|-------------------|------|-------------|--------------|
| 鉱物分類ID | id | int | PK | 自動採番 |
| 分類名 | name | varchar | UNIQUE, NOT NULL | 元素鉱物、珪酸塩鉱物など |
| 説明 | description | text | | 分類の概要 |
