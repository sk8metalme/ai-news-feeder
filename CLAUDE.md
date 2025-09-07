# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News Feeder is a Python application that monitors Hacker News for AI-related articles, verifies their credibility through fact-checking, summarizes them using Claude CLI, and sends notifications to Slack.

## Architecture

### Core Components
- **Main entry point**: `main.py` - CLI application with `--run-once` and `--schedule` modes
- **Scheduler**: `src/scheduler.py` - Orchestrates the verification pipeline
- **API Layer**: `src/api/hacker_news.py` - Hacker News API client
- **Verification**: `src/verification/fact_checker.py` - Fact-checking via dev.to and Medium
- **Summarization**: `src/utils/article_summarizer.py` - Claude CLI integration for Japanese summaries
- **Notification**: `src/notification/slack_notifier.py` - Slack webhook integration
- **Reporting**: `src/utils/report_generator.py` - JSON report generation

### Data Flow
1. HackerNewsAPI fetches top stories with score > 50
2. Articles filtered by AI keywords (ChatGPT, Claude, AI, LLM, etc.)
3. FactChecker verifies credibility via dev.to/Medium search
4. ArticleSummarizer generates Japanese summaries via Claude CLI
5. SlackNotifier sends formatted messages with verification status
6. ReportGenerator creates daily JSON reports in `data/`

## Development Commands

### Test Execution
```bash
# Run all tests (71 total)
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_hacker_news_api.py -v

# Custom test runner with dependency installation
./run_tests.py

# Run specific test via custom runner
./run_tests.py hacker_news_api
```

### Application Execution
```bash
# Single run (test mode)
python main.py --run-once

# Scheduled mode (default)
python main.py --schedule

# Install cron job for automation
./install_cron.sh
```

### Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables (.env)
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL (required)
- `SLACK_CHANNEL` - Slack channel (default: #ai-news)
- `ENABLE_SUMMARIZATION` - Enable Claude CLI summaries (default: true)
- `CLAUDE_CLI_PATH` - Path to Claude CLI binary (default: claude)
- `SUMMARIZATION_TIMEOUT` - Claude CLI timeout in seconds (default: 60)

### Settings (config/settings.py)
- `SCORE_THRESHOLD` - Minimum HN score (default: 50)
- `MAX_ARTICLES_PER_DAY` - Daily article limit (default: 5)
- `AI_KEYWORDS` - Keywords for article filtering
- `CHECK_INTERVAL_HOURS` - Verification interval (default: 24)

## Key Design Patterns

### Error Handling
- All modules use `src/utils/logger.py` for consistent logging
- Claude CLI failures gracefully degrade (no summarization)
- Network timeouts and API rate limits are handled
- Failed articles are logged but don't stop the pipeline

### Testing Strategy
- Mock external APIs (HN, dev.to, Medium, Slack)
- Test Claude CLI integration with subprocess mocking
- Separate unit and integration test markers
- pytest configuration in `pytest.ini`

### Extensibility Points
- New verification sources: extend `FactChecker`
- Additional keywords: modify `AI_KEYWORDS` in settings
- Custom notification formats: extend `SlackNotifier.format_verification_report()`
- New summarization backends: create alternative to `ArticleSummarizer`

## File Structure Conventions
- Source code in `src/` with package structure
- Tests mirror source structure in `tests/`
- Daily logs in `logs/ai_news_feeder_YYYYMMDD.log`
- JSON reports in `data/ai_news_report_YYYYMMDD.json`
- Configuration centralized in `config/settings.py`