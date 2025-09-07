# Changelog

All notable changes to AI News Feeder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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