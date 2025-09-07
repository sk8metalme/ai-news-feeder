"""テスト共通設定とフィクスチャ"""
import pytest
import os
import sys
from unittest.mock import Mock, patch

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 環境変数のモック
TEST_ENV = {
    'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/TEST/WEBHOOK/URL',
    'ARTICLES_PER_DAY': '5',
    'MINIMUM_SCORE': '50',
    'RUN_HOUR': '9'
}

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """テスト用環境変数を設定"""
    for key, value in TEST_ENV.items():
        monkeypatch.setenv(key, value)

@pytest.fixture
def mock_hackernews_response():
    """Hacker News APIレスポンスのモック"""
    return {
        'story_ids': [1001, 1002, 1003, 1004, 1005],
        'stories': [
            {
                'id': 1001,
                'title': 'ChatGPT-4 Achieves New Benchmark in Reasoning',
                'url': 'https://example.com/chatgpt-benchmark',
                'score': 256,
                'time': 1693900000,
                'type': 'story'
            },
            {
                'id': 1002,
                'title': 'Claude 3.5 Sonnet Released with Improved Capabilities',
                'url': 'https://example.com/claude-release',
                'score': 189,
                'time': 1693890000,
                'type': 'story'
            },
            {
                'id': 1003,
                'title': 'OpenAI Announces New Safety Research',
                'url': 'https://example.com/openai-safety',
                'score': 134,
                'time': 1693880000,
                'type': 'story'
            },
            {
                'id': 1004,
                'title': 'Deep Learning Framework Comparison 2025',
                'url': 'https://example.com/dl-comparison',
                'score': 98,
                'time': 1693870000,
                'type': 'story'
            },
            {
                'id': 1005,
                'title': 'Understanding LLM Hallucinations',
                'url': 'https://example.com/llm-hallucinations',
                'score': 87,
                'time': 1693860000,
                'type': 'story'
            }
        ]
    }

@pytest.fixture
def mock_factcheck_response():
    """ファクトチェックAPIレスポンスのモック"""
    return {
        'dev_to': [
            {
                'title': 'ChatGPT-4 Performance Analysis',
                'url': 'https://dev.to/user/chatgpt-analysis',
                'source': 'dev.to'
            },
            {
                'title': 'Benchmarking AI Models',
                'url': 'https://dev.to/user/ai-benchmarks',
                'source': 'dev.to'
            }
        ],
        'medium': [
            {
                'title': 'The Latest in ChatGPT Development',
                'url': 'https://medium.com/@user/chatgpt-dev',
                'source': 'Medium'
            }
        ]
    }

@pytest.fixture
def mock_slack_webhook():
    """Slack Webhookのモック"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'ok'
        mock_post.return_value = mock_response
        yield mock_post