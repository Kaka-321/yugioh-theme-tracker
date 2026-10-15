\# データ形式のルール



\## テーマ JSON の必須フィールド

\- `canonical\_name` (string) : 日本語名。必ず閉じ引用符を付ける

\- `canonical\_name\_en` (string) : 英語名

\- `theme\_id` (string) : 一意の ID

\- `aliases` (array) : 別名リスト。空でも必ず配列で存在させる

\- `source` (object) : `title` と `url` を必ず含む

\- `schema\_version` (string)



\## 禁止事項

\- `canonical\_name` に制御文字や不正な文字を入れない

\- `aliases` を省略しない（必ず `\[]` を入れる）

\- JSON 保存前に `ConvertFrom-Json` や `json.loads` で検証する



\## 過去に発生した問題

\- `canonical\_name` の閉じ引用符が欠落し、JSON が壊れた

\- 原因は文字エンコーディングの不備。必ず UTF-8 で保存すること

