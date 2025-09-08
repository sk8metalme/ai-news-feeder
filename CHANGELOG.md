# Changelog

All notable changes to AI News Feeder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2025-09-08

### Changed
- Code cleanup: unify GitHub/Reddit per-source dedup; remove global dedup
- Orchestrator wired to `.env` toggles (`ENABLE_REDDIT`, `ENABLE_GITHUB`, `MAX_ARTICLES_PER_SOURCE`)
- Claude CLI availability check hardened for sandboxed environments
- README updated to match `.env.example` and new integrations

### Deprecated
- `src/api/hackernews_api.py` (use `src/api/hacker_news.py`)
- `src/api/factcheck_api.py` (use `src/verification/fact_checker.py`)
- `src/utils/slack_notifier.py` (use `src/notification/slack_notifier.py`)

## [1.1.0] - 2025-09-06

### Added
- **ヘルスチェック機能**: システム稼働状況の監視（`scripts/health_monitor.py`）
  - 各コンポーネントの健全性チェック
  - API接続状況の監視
  - ヘルスチェック履歴の記録
- **異常検知・アラート機能**: 自動異常検知とSlack通知
  - 連続実行失敗の検知（3回以上）
  - 記事数不足の検知
  - パフォーマンス劣化の検知
  - ベースライン性能の自動計算
- **実行統計の可視化**: 統計レポート生成（`scripts/statistics_report.py`）
  - 日次・週次レポート
  - パフォーマンス分析
  - Slackダッシュボード機能
  - トレンド分析

### Changed
- NewsProcessorに実行結果記録機能を追加
- 処理時間の計測と記録

## [1.0.1] - 2025-09-06

### Added
- **信頼度スコアシステム**: 0.0-1.0の信頼度スコアを計算し、3段階（High/Medium/Low）で表示
- **柔軟なファクトチェック基準**: 環境変数で検証基準をカスタマイズ可能
- **A/Bテストツール**: `scripts/factcheck_analysis.py`で異なる設定の効果を分析
- **テストカバレッジ**: pytest導入、95%以上のカバレッジ目標設定

### Changed
- ファクトチェック判定ロジックを改善（記事数＋信頼度の複合判定）
- Slack通知フォーマットに信頼度レベルを追加
- 検証基準を環境変数で設定可能に

### Configuration
- `FACTCHECK_MIN_SOURCES`: 最低限必要な関連記事数（デフォルト: 1）
- `FACTCHECK_MIN_DEV_TO`: dev.toの最低記事数（デフォルト: 0）
- `FACTCHECK_MIN_MEDIUM`: Mediumの最低記事数（デフォルト: 0）
- `FACTCHECK_CONFIDENCE_THRESHOLD`: 信頼度閾値（デフォルト: 0.5）

## [1.0.0] - 2025-09-05

### Added
- 初回リリース（MVP版）
- Hacker News APIからのAI関連記事自動収集機能
- dev.to/Mediumでの信憑性検証機能
- Slack Webhook経由での自動投稿機能
- AIキーワードフィルタリング（ChatGPT, Claude, AI, LLM等）
- スコアベースのフィルタリング（デフォルト: 50点以上）
- 構造化レポート生成機能
- cron設定用スクリプト
- ローカルレポート保存機能

### Technical Details
- Python 3.x対応
- 主要ライブラリ: requests, beautifulsoup4, feedparser, schedule
- 環境変数による設定管理（.env）
- ログ出力機能

### Configuration
- `SLACK_WEBHOOK_URL`: Slack通知用Webhook URL
- `ARTICLES_PER_DAY`: 1日の投稿記事数（デフォルト: 5）
- `MINIMUM_SCORE`: 最低スコア閾値（デフォルト: 50）
- `RUN_HOUR`: 実行時刻（デフォルト: 9時）
