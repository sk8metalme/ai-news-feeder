# AI News Feeder Architecture (v1.4)

## Overview
- Sources: Hacker News (core), Reddit (optional), GitHub Trending (optional)
- Pipeline: Scheduler → Fetch → Verify (dev.to/Medium) → Summarize (Claude Code CLI) → Notify (Slack)
- Orchestration: `src/orchestrator/news_orchestrator.py`

## Modules
- Hacker News: `src/api/hacker_news.py` (canonical)
- Reddit: `src/api/reddit_api.py`
- GitHub: `src/api/github_trending.py`
- Fact Check: `src/verification/fact_checker.py`
- Notification: `src/notification/slack_notifier.py`
- Scheduling: `src/scheduler.py` (in-app), `cron`/`launchd` scripts

## Configuration
- `.env` → toggles and tokens
  - `ENABLE_REDDIT`, `ENABLE_GITHUB`, `MAX_ARTICLES_PER_SOURCE`
- `ENABLE_SUMMARIZATION`, `CLAUDE_CLI_PATH`, `SUMMARIZATION_TIMEOUT`, `ANTHROPIC_API_KEY`（cron運用時推奨）
- `config/settings.py` → app constants (keywords, thresholds)

## Deprecations (kept for compatibility)
- `src/api/hackernews_api.py` → use `src/api/hacker_news.py`
- `src/api/factcheck_api.py` → use `src/verification/fact_checker.py`
- `src/utils/slack_notifier.py` → use `src/notification/slack_notifier.py`

These modules emit `DeprecationWarning` and will be removed in a future release.
## Runtime & Scheduling

- Cron: `install_cron.sh` が `.env` をロードし、PATH/UTF-8 ロケールを注入。ワンショット（`--run-in-minutes`）と診断（`--claude-test-in-minutes`）をサポート。
- LaunchAgent (macOS): `scripts/setup_launchd.sh` でユーザーセッション内で実行（Keychain 認証可）。`--daily-at`/`--interval`/`--no-run-at-load` をサポート。

## Summarization Backend

- Claude Code CLI（`@anthropic-ai/claude-code`）の非対話モード（`-p/--output-format text`）を利用。
- `ArticleSummarizer` は複数の呼び出し戦略でフォールバック実行し、ANSI 除去・詳細ログ・可用性キャッシュを備える。

