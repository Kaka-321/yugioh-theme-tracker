# 遊戯王テーマ情報トラッカー

遊戯王のテーマ情報を整理する非公式プロジェクトです。
現在は「青眼」1テーマを対象とした最小構成で動作確認しています。

## 公開サイト

https://Kaka-321.github.io/yugioh-theme-tracker/

## 現在できること

- Yugipedia APIから、青眼ページの名前とURLを取得する
- 取得情報を30日間の有効期限でキャッシュする
- 正規化済みJSONを保存する
- 内容に変化がある場合だけJSONを更新する
- GitHub Actionsでデータ更新を実行する
- データ変更時にcommit・pushし、Pages公開を要求する
- 実行結果をArtifactとして14日間保存する
- GitHub Pagesでテーマ名、別名、出典リンクを表示する

## 自動取得と手動登録の区別

| 情報 | 登録方法 |
|---|---|
| 出典ページの名前・URL | Yugipedia API |
| 日本語テーマ名 | 手動 |
| 別名・通称 | 手動 |

関連カード一覧、カード効果、展開ルートなどは、
まだ自動収集していません。

カード画像やカードテキスト全文は掲載していません。
本プロジェクトはKONAMIの公式サービスではありません。

## 必要な環境

- Git
- GitHub CLI
- Python 3.12

現在のPythonプログラムは標準ライブラリのみを使用します。

## ローカルでの準備

リポジトリのルートで、次を実行します。

```powershell
py -3.12 -m venv .venv
```

## ローカルでの実行

```powershell
.\.venv\Scripts\python.exe crawler\main.py
```

接続・キャッシュ確認用のプログラム：

```powershell
.\.venv\Scripts\python.exe crawler\check_source.py
```

## ファイル構成

```text
.github/workflows/
  pages.yml              Pages公開
  update.yml             データ更新

crawler/
  main.py                公開JSON生成・差分判定・実行記録
  check_source.py        APIアクセス・キャッシュ読み込み

data/
  themes/blue-eyes.json   公開するテーマデータ
  internal/status.json   実行記録。Git管理対象外

.cache/
  yugipedia-blue-eyes.json
                         ローカルキャッシュ。Git管理対象外

site/
  index.html             公開ページ

docs/
  runbook.md             実行・障害対応手順
```

## 定期実行

- Workflow：Update Theme Data
- cron：23 18 * * *
- 目標時刻：毎日、日本時間午前3時23分
- 手動実行も可能

定期実行はベストエフォートです。
遅延・欠落が発生しても、公開サイトは前回のデータを表示します。

実行のたびにAPIへアクセスするわけではありません。
有効なキャッシュがある場合は、その情報を利用します。

## キャッシュ

ローカルとGitHub Actionsのキャッシュは別物です。

- ローカル：.cache/ に保存
- Actions：actions/cacheで保存・復元
- 情報の有効期限：30日
- キャッシュがない場合、または期限切れの場合に再取得

Actionsのキャッシュは永続保存ではありません。
削除された場合はAPIから再取得します。

## 公開処理

mainブランチに以下の変更をpushすると、
Deploy Pagesが起動します。

- site/**
- data/themes/**
- .github/workflows/pages.yml

Update Theme Dataによるデータ変更時は、
Pagesの手動実行イベントを明示的に呼び出します。

crawler/やdocs/だけの変更では、
Pages公開は自動起動しません。

## 実行記録と公開範囲

実行記録では、次を区別します。
- started_at / finished_at：今回の実行日時
- source_fetched_at：APIから実際に取得した日時
- source_used：api または cache
- content_changed：公開JSONが変わったか

日時はUTCで記録します。

data/internal/status.jsonはPagesには公開しません。
ただし、Actionsに保存するArtifactやログは、
Publicリポジトリの非公開保管場所ではありません。

パスワード、APIキー、個人情報は入れないでください。

## 現在の未実装項目

- 外部監視・通知
- 長期無活動対策の週次heartbeat
- 公開用status.json
- JSON Schemaによるデータ検証
- 複数テーマへの対応
- 関連カード情報の取得
- 権利・削除要請の正式な連絡窓口

Publicリポジトリの定期Workflowは、
60日間リポジトリ活動がない場合に無効化される可能性があります。
定期実行が動くだけで、永久に維持される前提にはしません。

## 運用手順

[Runbook](docs/runbook.md)を参照してください。
