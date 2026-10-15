# プロジェクト概要

## 目的
遊戯王のテーマ情報を整理・表示する非公式サイト。
Yugipedia API からデータを取得し、静的 JSON として保存。
フロントエンドは素の HTMLCSSJS で表示する。

## 構成
- `site`  フロントエンド（index.html, themes.json）
- `datathemes`  テーマごとの JSON ファイル
- データ取得は Python スクリプトで行う

## 絶対に守る前提
- データは必ず UTF-8 で保存する
- JSON は必ず構文チェックしてから保存する
- API 呼び出しは Python で行う（PowerShell は使わない）