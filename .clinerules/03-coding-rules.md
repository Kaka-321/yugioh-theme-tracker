# コーディングルール

## フロントエンド（index.html）
- 素の JavaScript を使う（フレームワーク禁止）
- `fetch` で JSON を読み込む際は、必ずエラーハンドリングを入れる
- データ検証では、`aliases` が配列であることを必ず確認する

## バックエンド（Python）
- API 呼び出しには `requests` を使う
- URL クエリは `params` 辞書で渡す（手動で文字列連結しない）
- レスポンスは必ず `response.json()` でパースし、失敗時はログを残す

## PowerShell の制限
- コマンドが長くなる場合は、必ずスクリプトファイルに書き出してから実行する
- `Invoke-WebRequest` を使う場合は `-UseBasicParsing` を付ける