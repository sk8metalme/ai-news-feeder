# Phase 3: Reddit/GitHub Orchestration + Notifications & Summarization Improvements

## Summary
This PR delivers Phase 3 integration and productionization:

- Add full-source orchestration (Hacker News + optional Reddit/GitHub) controlled by .env toggles.
- Add flexible notifications policy (verified_only | verified_or_partial | all) to control Slack delivery.
- Make summarization configurable; enable Claude CLI summaries with non‑text guard.
- Stabilize GitHub/Reddit per-source dedup; avoid over-aggressive global dedup at API layer.
- Remove legacy modules; unify on new APIs; update docs.
- End-to-end production checks: health check + one-off runs verified with Slack delivery.

## Key Changes
- Orchestrator
  - `src/orchestrator/news_orchestrator.py`: Enable sources via `ENABLE_REDDIT`, `ENABLE_GITHUB`, cap via `MAX_ARTICLES_PER_SOURCE`.
  - Honor `NOTIFY_VERIFICATION_LEVEL` for per-article Slack notifications.
- Scheduler
  - `src/scheduler.py`: Same notification policy applied to single-run workflow.
- Reddit/GitHub APIs
  - `src/api/reddit_api.py`: `REDDIT_SCORE_THRESHOLD` (default 40) and per-subreddit dedup; use settings by default.
  - `src/api/github_trending.py`: Per-language dedup; import changed for easier test patching.
- Summarization
  - `src/utils/article_summarizer.py`: Skip non-text content; keep summaries short; configurable by `ENABLE_SUMMARIZATION`.
- Settings / Env
  - `config/settings.py`: Add `REDDIT_SCORE_THRESHOLD`, `NOTIFY_VERIFICATION_LEVEL`.
  - `.env.example`: Updated with new toggles and policy; sample shows `NOTIFY_VERIFICATION_LEVEL=all`.
- Cleanup / Deprecations
  - Remove legacy modules: `src/api/hackernews_api.py`, `src/api/factcheck_api.py`, `src/utils/slack_notifier.py`, `src/utils/config.py`.
  - Update tests to use `src/api/hacker_news.py`.
- Docs
  - `README.md`, `CHANGELOG.md`, `specs/001-reddit-api-github/spec.md` updated.
  - New `docs/ARCHITECTURE.md` (v1.3 overview, modules, toggles, and deprecations).

## Tests
- `pytest`: 126 passed, 1 skipped.
- Updated tests: `tests/test_hackernews_api.py`, `tests/test_reddit_api.py`.

## Production Verification
- Health check run → Slack report OK.
- One-off runs:
  - HN only / with summarization off → OK (verified + summary messages)
  - HN+Reddit (low caps, score threshold 40) → OK
  - Summarization enabled end-to-end → summaries present in Slack
- Cron installed: daily at 09:00 (see `install_cron.sh`).

## Migration Notes
- Depending modules should import:
  - HN: `src/api/hacker_news.HackerNewsAPI`
  - Fact checker: `src/verification/fact_checker.FactChecker`
  - Slack: `src/notification/slack_notifier.SlackNotifier`
- Configure via `.env`:
  - `ENABLE_REDDIT`, `ENABLE_GITHUB`, `MAX_ARTICLES_PER_SOURCE`
  - `REDDIT_SCORE_THRESHOLD`
  - `ENABLE_SUMMARIZATION`
  - `NOTIFY_VERIFICATION_LEVEL`

## Rollout Recommendations
- Start with `NOTIFY_VERIFICATION_LEVEL=verified_or_partial` to limit noise.
- Adjust `MAX_ARTICLES_PER_SOURCE` and `REDDIT_SCORE_THRESHOLD` based on daily volume.
- Keep `ENABLE_SUMMARIZATION=true` for better signal; skip for high-traffic hours if needed.

