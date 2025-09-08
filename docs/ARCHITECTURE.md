# AI News Feeder Architecture (v1.3)

## Overview
- Sources: Hacker News (core), Reddit (optional), GitHub Trending (optional)
- Pipeline: Scheduler → Fetch → Verify (dev.to/Medium) → Summarize (Claude) → Notify (Slack)
- Orchestration: `src/orchestrator/news_orchestrator.py`

## Modules
- Hacker News: `src/api/hacker_news.py` (canonical)
- Reddit: `src/api/reddit_api.py`
- GitHub: `src/api/github_trending.py`
- Fact Check: `src/verification/fact_checker.py`
- Notification: `src/notification/slack_notifier.py`
- Scheduling: `src/scheduler.py`

## Configuration
- `.env` → toggles and tokens
  - `ENABLE_REDDIT`, `ENABLE_GITHUB`, `MAX_ARTICLES_PER_SOURCE`
  - `ENABLE_SUMMARIZATION`, `CLAUDE_CLI_PATH`, `SUMMARIZATION_TIMEOUT`
- `config/settings.py` → app constants (keywords, thresholds)

## Deprecations (kept for compatibility)
- `src/api/hackernews_api.py` → use `src/api/hacker_news.py`
- `src/api/factcheck_api.py` → use `src/verification/fact_checker.py`
- `src/utils/slack_notifier.py` → use `src/notification/slack_notifier.py`

These modules emit `DeprecationWarning` and will be removed in a future release.

