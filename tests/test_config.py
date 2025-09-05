"""
Tests for configuration settings
"""
import pytest
import os
from unittest.mock import patch

# Test configuration module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import settings


class TestConfiguration:
    """Test cases for configuration settings"""
    
    def test_hacker_news_api_url(self):
        """Test Hacker News API URL configuration"""
        assert settings.HACKER_NEWS_API_URL == "https://hacker-news.firebaseio.com/v0"
    
    def test_score_threshold(self):
        """Test score threshold configuration"""
        assert settings.SCORE_THRESHOLD == 50
        assert isinstance(settings.SCORE_THRESHOLD, int)
    
    def test_ai_keywords(self):
        """Test AI keywords configuration"""
        assert isinstance(settings.AI_KEYWORDS, list)
        assert len(settings.AI_KEYWORDS) > 0
        
        # Check that expected keywords are present
        expected_keywords = ["ChatGPT", "Claude", "AI", "LLM", "OpenAI", "Google AI"]
        for keyword in expected_keywords:
            assert keyword in settings.AI_KEYWORDS
    
    def test_dev_to_api_url(self):
        """Test dev.to API URL configuration"""
        assert settings.DEV_TO_API_URL == "https://dev.to/api/articles"
    
    def test_medium_rss_url(self):
        """Test Medium RSS URL template"""
        assert "{tag}" in settings.MEDIUM_RSS_URL
        assert "medium.com" in settings.MEDIUM_RSS_URL
    
    def test_max_articles_per_day(self):
        """Test maximum articles per day setting"""
        assert settings.MAX_ARTICLES_PER_DAY == 5
        assert isinstance(settings.MAX_ARTICLES_PER_DAY, int)
    
    def test_check_interval_hours(self):
        """Test check interval configuration"""
        assert settings.CHECK_INTERVAL_HOURS == 24
        assert isinstance(settings.CHECK_INTERVAL_HOURS, int)
    
    @patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/test'})
    def test_slack_webhook_url_from_env(self):
        """Test Slack webhook URL from environment variable"""
        # Reload the module to pick up the environment variable
        import importlib
        importlib.reload(settings)
        
        assert settings.SLACK_WEBHOOK_URL == 'https://hooks.slack.com/test'
    
    @patch.dict(os.environ, {'SLACK_CHANNEL': '#test-channel'})
    def test_slack_channel_from_env(self):
        """Test Slack channel from environment variable"""
        import importlib
        importlib.reload(settings)
        
        assert settings.SLACK_CHANNEL == '#test-channel'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_slack_channel_default(self):
        """Test default Slack channel when not set"""
        import importlib
        importlib.reload(settings)
        
        assert settings.SLACK_CHANNEL == "#ai-news"
    
    def test_log_dir(self):
        """Test log directory configuration"""
        assert settings.LOG_DIR == "logs"
    
    def test_data_dir(self):
        """Test data directory configuration"""
        assert settings.DATA_DIR == "data"
