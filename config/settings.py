"""
Configuration settings for AI News Feeder
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Hacker News API settings
HACKER_NEWS_API_URL = "https://hacker-news.firebaseio.com/v0"
SCORE_THRESHOLD = 50

# AI-related keywords for filtering
AI_KEYWORDS = [
    "ChatGPT", "Claude", "AI", "LLM", "OpenAI", "Google AI", 
    "artificial intelligence", "machine learning", "deep learning",
    "GPT", "neural network", "transformer"
]

# External verification sources
DEV_TO_API_URL = "https://dev.to/api/articles"
MEDIUM_RSS_URL = "https://medium.com/feed/tag/{tag}"

# Slack settings
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#ai-news")

# Timing settings
CHECK_INTERVAL_HOURS = 24
MAX_ARTICLES_PER_DAY = 5

# Article summarization settings
ENABLE_SUMMARIZATION = os.getenv("ENABLE_SUMMARIZATION", "true").lower() == "true"
CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")
SUMMARIZATION_TIMEOUT = int(os.getenv("SUMMARIZATION_TIMEOUT", "120"))  # seconds (increased from 60)
CLAUDE_MIN_REQUEST_INTERVAL_SECONDS = float(os.getenv("CLAUDE_MIN_REQUEST_INTERVAL_SECONDS", "5.0"))  # rate limiting
CLAUDE_MAX_PROMPT_CHARS = int(os.getenv("CLAUDE_MAX_PROMPT_CHARS", "4000"))  # prompt length limit

# File paths
LOG_DIR = "logs"
DATA_DIR = "data"

# Source toggles
ENABLE_REDDIT = os.getenv("ENABLE_REDDIT", "true").lower() == "true"
ENABLE_GITHUB = os.getenv("ENABLE_GITHUB", "true").lower() == "true"
MAX_ARTICLES_PER_SOURCE = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "5"))

# Reddit filtering
REDDIT_SCORE_THRESHOLD = int(os.getenv("REDDIT_SCORE_THRESHOLD", "40"))

# Notification behavior
# one of: 'verified_only', 'verified_or_partial', 'all'
NOTIFY_VERIFICATION_LEVEL = os.getenv("NOTIFY_VERIFICATION_LEVEL", "verified_only").lower()

# Title translation (Slack display)
TRANSLATE_TITLES = os.getenv("TRANSLATE_TITLES", "true").lower() == "true"
SLACK_JA_UI = os.getenv("SLACK_JA_UI", "false").lower() == "true"
