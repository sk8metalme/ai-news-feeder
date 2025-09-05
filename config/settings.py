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

# File paths
LOG_DIR = "logs"
DATA_DIR = "data"
