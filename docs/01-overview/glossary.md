# 用語集 (Glossary)

## 📚 プロジェクト固有用語

### A

**AI Keywords**  
AI関連記事を識別するためのキーワードリスト。`config/settings.py`で定義され、"ChatGPT", "Claude", "AI", "LLM"等を含む。

**Article Summarizer**  
Claude CLIを使用して記事の日本語要約を生成するモジュール（`src/utils/article_summarizer.py`）。

### C

**Claude CLI**  
Anthropic社のClaude AIをコマンドラインから利用するツール。記事要約機能で使用。

**Cron運用**  
`install_cron.sh`を使用したスケジューリング方式。`.env`をロードし、PATH/UTF-8ロケールを注入。

### F

**Fact Checker**  
dev.toとMedium RSSを使用して記事の信憑性を検証するモジュール（`src/verification/fact_checker.py`）。

### H

**Hacker News API**  
Hacker Newsのトップストーリーを取得するAPI。プロジェクトの主要データソース。

**Health Checker**  
システムの稼働状況を監視するモジュール（`src/utils/health_checker.py`）。

### L

**LaunchAgent運用**  
macOS専用のスケジューリング方式。Keychain認証を利用してAPIキーを`.env`に保存せずに運用可能。

### O

**Orchestrator**  
複数のニュースソース（Hacker News、Reddit、GitHub）を統合管理するモジュール（`src/orchestrator/news_orchestrator.py`）。

### R

**Reddit API**  
Reddit投稿を取得するAPI。PRAW（Python Reddit API Wrapper）を使用。

### S

**Score Threshold**  
記事の品質を判定するスコア閾値。Hacker Newsでは50点以上、Redditでは40点以上がデフォルト。

**Slack Notifier**  
Slackへの通知を管理するモジュール（`src/notification/slack_notifier.py`）。

## 🔧 技術用語

### API関連

**Rate Limiting**  
API呼び出し頻度の制限。Hacker News: 0.1秒間隔、Reddit: 60req/分、GitHub: 5,000req/時。

**Webhook**  
SlackのIncoming Webhook機能。通知配信に使用。

### 開発・運用

**CI/CD**  
継続的インテグレーション・継続的デプロイメント。GitHub Actionsでの実装を計画中。

**Test Coverage**  
テストカバレッジ。現在94%（67/71テスト成功）。

**Technical Debt**  
技術的負債。テストコード品質、エラーハンドリング統一等が対象。

### データ処理

**Deduplication**  
重複記事の除去処理。URL正規化による重複検知を実装。

**Verification Status**  
記事の検証状態。"verified"（検証済み）、"unverified"（未検証）、"partial"（部分検証）。

## 📊 設定・環境変数

### 必須設定

**SLACK_WEBHOOK_URL**  
Slack通知用のWebhook URL。

**SLACK_CHANNEL**  
通知先Slackチャンネル（デフォルト: #ai-news）。

### オプション設定

**ENABLE_SUMMARIZATION**  
記事要約機能の有効/無効（デフォルト: true）。

**CLAUDE_CLI_PATH**  
Claude CLIの実行パス（デフォルト: claude）。

**ANTHROPIC_API_KEY**  
Anthropic APIキー。cron運用時に推奨。

**ENABLE_REDDIT**  
Reddit連携の有効/無効（デフォルト: true）。

**ENABLE_GITHUB**  
GitHub連携の有効/無効（デフォルト: true）。

**MAX_ARTICLES_PER_SOURCE**  
各ソースからの最大記事数（デフォルト: 5）。

## 🗂️ ファイル・ディレクトリ

### 設定ファイル

**`.env`**  
環境変数設定ファイル。APIキーや機能フラグを定義。

**`config/settings.py`**  
アプリケーション設定。キーワード、閾値、URL等を定義。

### ログ・データ

**`logs/ai_news_feeder_YYYYMMDD.log`**  
日次ローテーションログファイル。

**`data/ai_news_report_YYYYMMDD.json`**  
日次レポートのJSON形式データ。

### スクリプト

**`install_cron.sh`**  
cron設定用スクリプト。ワンショット実行と診断機能を提供。

**`scripts/setup_launchd.sh`**  
macOS LaunchAgent管理スクリプト。

**`scripts/claude_cli_doctor.sh`**  
Claude CLI診断スクリプト。

## 🎯 ビジネス用語

### KPI・指標

**Processing Time**  
記事処理時間。5記事を5分以内が目標。

**Verification Rate**  
記事検証率。関連記事1件以上で「検証済み」判定。

**Summarization Success Rate**  
要約成功率。80%以上が目標。

### フェーズ・マイルストーン

**Phase 1**  
安定化・最適化フェーズ（2-3週間）。

**Phase 2**  
パフォーマンス向上フェーズ（3-4週間）。

**Phase 3**  
機能拡張フェーズ（5週間）。Reddit・GitHub連携実装。

**Phase 4**  
UI・UX向上フェーズ（4-8週間）。

## 🔄 プロセス用語

### 開発プロセス

**Sprint**  
2週間の開発サイクル。

**Technical Debt Sprint**  
技術的負債対応のための時間。全体の20%を割り当て。

**Go/No-Go判断**  
本格運用開始の判定プロセス。

### 運用プロセス

**Health Check**  
システム稼働状況の定期確認。

**Incident Response**  
障害対応プロセス。24/7対応可能な体制を目標。

**Performance Monitoring**  
パフォーマンス監視。処理時間、成功率等を追跡。

---

**最終更新**: 2025-09-23  
**責任者**: ドキュメント管理チーム  
