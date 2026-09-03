### acquisition_methods（入手経路）

| カラム名（論理名） | カラム名（物理名） | type | constraints | 運用イメージ |
|-------------------|-------------------|------|-------------|--------------|
| 入手経路ID | id | int | PK | 自動採番 |
| 名称 | name | varchar | UNIQUE, NOT NULL | 採集、購入、交換、譲渡など |
| 説明 | description | text | | 必要に応じて運用ルールを記載 |
