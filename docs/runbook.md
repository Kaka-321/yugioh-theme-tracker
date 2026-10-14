# Runbook：実行・障害対応手順

## 1. 基本方針

- 更新失敗とサイト停止は別の問題として扱う
- 更新に失敗しても、前回公開したデータを残す
- エラーログを確認してから修正・再実行する
- APIエラー時に連続で再試行しない
- キャッシュを理由なく削除しない
- 完全な無人自動復旧は保証しない

## 2. 作業を始める

PowerShellで、リポジトリのルートへ移動します。

```powershell
Set-Location "$HOME\Projects\yugioh-theme-tracker"
git status
git pull --ff-only
```

未保存の変更がある場合は、上書きやリセットをせず、
変更内容を確認してください。

Actionsがデータをcommitした場合も、
次回のローカル作業前にpullします。

## 3. ローカル実行

```powershell
.\.venv\Scripts\python.exe crawler\main.py
```

正常な表示例：

```text
SOURCE: cache
UNCHANGED: data/themes/blue-eyes.json
STATUS: saved internal execution report
```

SOURCE: APIは、新たにAPIから取得したことを意味します。

UPDATEDは、公開JSONの内容が変わったことを意味します。
UNCHANGEDは、公開JSONの内容が同じだったことを意味します。

## 4. データ更新Workflowを手動実行する

```powershell
gh workflow run update.yml --repo Kaka-321/yugioh-theme-tracker
```

実行一覧を確認します。

```powershell
gh run list --repo Kaka-321/yugioh-theme-tracker --workflow update.yml --limit 5
```

同じWorkflowを必要なく何度も起動しないでください。

## 5. ログを確認する

以下のRUN_IDは、実行一覧のID欄の数字に置き換えます。

```powershell
gh run view RUN_ID --repo Kaka-321/yugioh-theme-tracker
```

全ログ：

```powershell
gh run view RUN_ID --repo Kaka-321/yugioh-theme-tracker --log
```

失敗したステップのログ：

```powershell
gh run view RUN_ID --repo Kaka-321/yugioh-theme-tracker --log-failed
```

実行中の場合、ログがまだ取得できないことがあります。
ブラウザで確認する場合：

```powershell
gh run view RUN_ID --repo Kaka-321/yugioh-theme-tracker --web
```

## 6. 実行記録を確認する

### ローカル

```powershell
Get-Content -Encoding utf8 data\internal\status.json
```

### GitHub Actions

1. Actionsを開く
2. Update Theme Dataの対象実行を開く
3. 概要画面のArtifactsへ進む
4. execution-reportをダウンロードする
5. ZIPを展開し、status.jsonを確認する

保存期間は14日です。

Artifactは非公開保管場所ではありません。
秘密情報を保存しないでください。

### フィールドの意味

| 項目 | 意味 |
|---|---|
| result | プログラムの成功・失敗 |
| source_used | api / cache |
| source_fetched_at | APIから取得した日時 |
| started_at | 実行開始日時 |
| finished_at | 実行終了日時 |
| content_changed | 公開JSONの内容に変更があったか |
| error_type | 失敗時の例外の種類 |

resultがsuccessでも、後続のgit pushやPages公開が
成功したとは限りません。
Workflow全体とDeploy Pagesの結果も確認してください。

## 7. Pages公開を確認する

```powershell
gh run list --repo Kaka-321/yugioh-theme-tracker --workflow pages.yml --limit 5
```

成功後、次のページを開きます。

https://Kaka-321.github.io/yugioh-theme-tracker/

確認項目：

- 青眼と別名が表示される
- 出典リンクが表示される
- 「テーマ情報と出典を読み込みました。」が表示される

古い表示が残る場合は、Ctrl + F5で再読み込みします。

## 8. Pagesがタイムアウトした場合

症状例：

```text
Current status: updating_pages
Error: Timeout reached, aborting!
```

手順：

1. 失敗したログを確認する
2. ファイル準備・アップロードまで成功しているか確認する
3. 少し待ち、Pagesの失敗した実行だけを一度再実行する
4. 再度失敗する場合は、連続再実行せず原因を調べる

再実行：

```powershell
gh run rerun RUN_ID --repo Kaka-321/yugioh-theme-tracker
```

進行状況：

```powershell
gh run watch RUN_ID --repo Kaka-321/yugioh-theme-tracker
```

リポジトリやPages設定を安易に作り直さないでください。

## 9. Pages設定が見つからないエラー

症状例：

```text
Get Pages site failed
Error: Not Found
```

確認：

1. リポジトリのSettingsを開く
2. Pagesを開く
3. Build and deploymentのSourceを確認する
4. GitHub Actionsが選択されていることを確認する
5. 設定確認後に公開処理を再実行する

## 10. API取得に失敗した場合

- 公開JSONを空データで置き換えない
- 既存キャッシュを安易に削除しない
- エラーの種類とActionsログを確認する
- 403 / 429の場合は連続再試行しない
- アクセス制限を回避するためのIP変更などは行わない
- 必要に応じて取得先のAPI利用条件を再確認する

更新Workflowが失敗しても、
既存の公開ページをそのまま残します。

## 11. 定期実行が見当たらない場合

```powershell
gh run list --repo Kaka-321/yugioh-theme-tracker --workflow update.yml --limit 10
gh workflow list --repo Kaka-321/yugioh-theme-tracker --all
```

確認項目：

- update.ymlがmainブランチにあるか
- schedule設定が保存されているか
- Workflowが無効化されていないか
- GitHub側で遅延が発生していないか

無効化されている場合は、原因確認後に有効化します。

```powershell
gh workflow enable update.yml --repo Kaka-321/yugioh-theme-tracker
```

その後、手動実行して正常動作を確認します。

週次heartbeatと外部監視は、現時点では未実装です。

## 12. ローカルの変更を保存する

必ず先に変更内容を確認します。

```powershell
git status
git diff
```

公開してよいファイルだけを明示的に追加してください。

例：

```powershell
git add crawler/main.py data/themes/blue-eyes.json
git commit -m "fix: update theme data handling"
git push
```

.venv/、.cache/、data/internal/、.envは
Git管理対象にしません。

パスワード、認証コード、トークンを
README・ログ・チャットなどへ貼らないでください。
