"""統合テスト - 全体的なワークフローをテスト"""
import pytest
from unittest.mock import patch, Mock
import time
import responses
from src.processing.news_processor import NewsProcessor


class TestIntegration:
    """システム全体の統合テスト"""
    
    @pytest.fixture
    def mock_current_time(self):
        """現在時刻のモック"""
        return 1693900000  # 2023-09-05 12:00:00
    
    @responses.activate
    @patch('time.time')
    @patch('feedparser.parse')
    def test_full_workflow_success(self, mock_feedparser, mock_time, mock_current_time):
        """完全なワークフローの成功テスト"""
        mock_time.return_value = mock_current_time
        
        # Hacker News APIのモック
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            json=[1001, 1002, 1003, 1004, 1005],
            status=200
        )
        
        # ストーリー詳細のモック
        stories = [
            {
                'id': 1001,
                'title': 'Revolutionary ChatGPT-5 Announced with AGI Capabilities',
                'url': 'https://example.com/chatgpt5',
                'score': 450,
                'time': mock_current_time - 3600,
                'type': 'story'
            },
            {
                'id': 1002,
                'title': 'Claude 3 Breaks New Ground in Code Generation',
                'url': 'https://example.com/claude3',
                'score': 320,
                'time': mock_current_time - 7200,
                'type': 'story'
            },
            {
                'id': 1003,
                'title': 'Regular Programming News',
                'url': 'https://example.com/programming',
                'score': 200,
                'time': mock_current_time - 10800,
                'type': 'story'
            },
            {
                'id': 1004,
                'title': 'OpenAI Releases New Safety Guidelines',
                'url': 'https://example.com/openai-safety',
                'score': 180,
                'time': mock_current_time - 14400,
                'type': 'story'
            },
            {
                'id': 1005,
                'title': 'Machine Learning Framework Updates',
                'url': 'https://example.com/ml-updates',
                'score': 90,
                'time': mock_current_time - 18000,
                'type': 'story'
            }
        ]
        
        for story in stories:
            responses.add(
                responses.GET,
                f"https://hacker-news.firebaseio.com/v0/item/{story['id']}.json",
                json=story,
                status=200
            )
        
        # dev.to APIのモック
        dev_to_response = [
            {
                'title': 'ChatGPT-5 Technical Analysis',
                'url': 'https://dev.to/user/chatgpt5-analysis',
                'tags': ['ai', 'chatgpt']
            },
            {
                'title': 'Understanding Claude 3 Architecture',
                'url': 'https://dev.to/user/claude3-arch',
                'tags': ['ai', 'claude']
            }
        ]
        
        # すべてのdev.to API呼び出しに対してレスポンスを設定
        for _ in range(20):  # 十分な数のレスポンスを設定
            responses.add(
                responses.GET,
                "https://dev.to/api/articles",
                json=dev_to_response,
                status=200
            )
        
        # Medium RSSフィードのモック
        mock_feed = Mock()
        mock_feed.bozo = False
        mock_feed.entries = [
            Mock(
                title='ChatGPT-5: A Deep Dive',
                link='https://medium.com/@ai/chatgpt5-deepdive',
                summary='Analysis of ChatGPT-5'
            ),
            Mock(
                title='Claude 3 in Production',
                link='https://medium.com/@dev/claude3-production',
                summary='Using Claude 3 effectively'
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        # Slack Webhookのモック
        responses.add(
            responses.POST,
            "https://hooks.slack.com/services/TEST/WEBHOOK/URL",
            status=200
        )
        
        # 処理を実行
        processor = NewsProcessor()
        result = processor.process_daily_news()
        
        # 結果を検証
        assert result is True
        
        # API呼び出しを確認
        hn_calls = [call for call in responses.calls if 'hacker-news' in call.request.url]
        assert len(hn_calls) >= 6  # topstories + 各ストーリー
        
        slack_calls = [call for call in responses.calls if 'slack.com' in call.request.url]
        assert len(slack_calls) == 1
        
        # Slackペイロードを確認
        slack_payload = slack_calls[0].request.body
        assert b'ChatGPT-5' in slack_payload or b'Claude 3' in slack_payload
        assert b'Verified' in slack_payload
    
    @responses.activate
    @patch('time.time')
    def test_workflow_with_no_ai_articles(self, mock_time, mock_current_time):
        """AI記事が見つからない場合のワークフロー"""
        mock_time.return_value = mock_current_time
        
        # Hacker News APIのモック
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            json=[2001, 2002],
            status=200
        )
        
        # AI関連でないストーリー
        non_ai_stories = [
            {
                'id': 2001,
                'title': 'JavaScript Framework Released',
                'url': 'https://example.com/js-framework',
                'score': 300,
                'time': mock_current_time - 3600,
                'type': 'story'
            },
            {
                'id': 2002,
                'title': 'Database Performance Tips',
                'url': 'https://example.com/db-tips',
                'score': 250,
                'time': mock_current_time - 7200,
                'type': 'story'
            }
        ]
        
        for story in non_ai_stories:
            responses.add(
                responses.GET,
                f"https://hacker-news.firebaseio.com/v0/item/{story['id']}.json",
                json=story,
                status=200
            )
        
        # Slack Webhookのモック（エラー通知用）
        responses.add(
            responses.POST,
            "https://hooks.slack.com/services/TEST/WEBHOOK/URL",
            status=200
        )
        
        # 処理を実行
        processor = NewsProcessor()
        result = processor.process_daily_news()
        
        # 結果を検証
        assert result is False
    
    @responses.activate
    def test_workflow_with_api_errors(self):
        """API エラーが発生した場合のワークフロー"""
        # Hacker News APIがエラーを返す
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            status=500
        )
        
        # Slack Webhookのモック（エラー通知用）
        responses.add(
            responses.POST,
            "https://hooks.slack.com/services/TEST/WEBHOOK/URL",
            status=200
        )
        
        # 処理を実行
        processor = NewsProcessor()
        result = processor.process_daily_news()
        
        # 結果を検証
        assert result is False
        
        # エラー通知が送信されたことを確認
        slack_calls = [call for call in responses.calls if 'slack.com' in call.request.url]
        assert len(slack_calls) == 1
        assert b'Error' in slack_calls[0].request.body or b'error' in slack_calls[0].request.body