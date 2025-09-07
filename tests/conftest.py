"""
pytest configuration and fixtures
"""
import sys
import os
import pytest
from unittest.mock import Mock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def sample_hn_story():
    """Sample Hacker News story data"""
    return {
        "id": 12345,
        "title": "New AI Model Breakthrough: ChatGPT-5 Released",
        "url": "https://example.com/chatgpt5-released",
        "score": 150,
        "time": 1640995200,  # 2022-01-01 00:00:00
        "by": "user123",
        "descendants": 50,
        "type": "story"
    }


@pytest.fixture
def sample_verification_result():
    """Sample verification result data"""
    return {
        "article_title": "New AI Model Breakthrough: ChatGPT-5 Released",
        "article_url": "https://example.com/chatgpt5-released",
        "verification_status": "verified",
        "related_articles": {
            "dev_to": [
                {
                    "title": "ChatGPT-5: What We Know So Far",
                    "url": "https://dev.to/article1",
                    "source": "dev.to",
                    "published_at": "2022-01-01T00:00:00Z"
                }
            ],
            "medium": [
                {
                    "title": "OpenAI Releases ChatGPT-5",
                    "url": "https://medium.com/article1",
                    "source": "medium",
                    "published_at": "2022-01-01T00:00:00Z"
                }
            ]
        },
        "total_related_count": 2,
        "checked_at": "2022-01-01 12:00:00 JST"
    }


@pytest.fixture
def mock_requests(mocker):
    """Mock requests module"""
    return mocker.patch('requests.get')


@pytest.fixture
def mock_slack_webhook(mocker):
    """Mock Slack webhook requests"""
    return mocker.patch('requests.post')


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary directory for test data"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return str(data_dir)
