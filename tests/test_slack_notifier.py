"""slack_notifier.pyのテスト"""
import pytest
from unittest.mock import Mock, patch
import responses
from datetime import datetime
from src.utils.slack_notifier import SlackNotifier


class TestSlackNotifier:
    """SlackNotifierクラスのテスト"""
    
    @pytest.fixture
    def notifier(self):
        """SlackNotifierインスタンスを返す"""
        return SlackNotifier()
    
    @pytest.fixture
    def sample_articles(self):
        """テスト用の記事データ"""
        return [
            {
                'title': 'ChatGPT-4 Achieves New Benchmark',
                'url': 'https://example.com/chatgpt',
                'score': 256,
                'time': 1693900000,
                'verification': {
                    'verified': True,
                    'related_count': 3,
                    'dev_to_count': 2,
                    'medium_count': 1,
                    'confidence_score': 0.85,
                    'sources': {
                        'dev_to': [
                            {'title': 'Related 1', 'url': 'https://dev.to/1'},
                            {'title': 'Related 2', 'url': 'https://dev.to/2'}
                        ],
                        'medium': [
                            {'title': 'Related 3', 'url': 'https://medium.com/1'}
                        ]
                    }
                }
            },
            {
                'title': 'Claude 3.5 Released',
                'url': 'https://example.com/claude',
                'score': 189,
                'time': 1693890000,
                'verification': {
                    'verified': False,
                    'related_count': 0,
                    'dev_to_count': 0,
                    'medium_count': 0,
                    'confidence_score': 0.0,
                    'sources': {'dev_to': [], 'medium': []}
                }
            }
        ]
    
    @responses.activate
    def test_send_verification_report_success(self, notifier, sample_articles):
        """検証レポートの送信が成功することを確認"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=200
        )
        
        result = notifier.send_verification_report(sample_articles)
        
        assert result is True
        assert len(responses.calls) == 1
        
        # 送信されたペイロードを確認
        request_body = responses.calls[0].request.body
        assert b'AI News Verification Report' in request_body
        assert b'ChatGPT-4 Achieves New Benchmark' in request_body
        assert b'Claude 3.5 Released' in request_body
    
    @responses.activate
    def test_send_verification_report_failure(self, notifier, sample_articles):
        """検証レポート送信失敗時の処理を確認"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=400
        )
        
        result = notifier.send_verification_report(sample_articles)
        assert result is False
    
    @responses.activate
    def test_send_verification_report_exception(self, notifier, sample_articles):
        """検証レポート送信時の例外処理を確認"""
        # responses.addを追加せずに呼び出すことで例外を発生させる
        result = notifier.send_verification_report(sample_articles)
        assert result is False
    
    def test_create_article_blocks_verified(self, notifier):
        """検証済み記事のブロック作成を確認"""
        article = {
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'score': 100,
            'verification': {
                'verified': True,
                'related_count': 2,
                'dev_to_count': 1,
                'medium_count': 1,
                'confidence_score': 0.75
            }
        }
        
        blocks = notifier._create_article_blocks(article)
        
        # ブロックの構造を確認
        assert len(blocks) > 0
        assert any('Test Article' in str(block) for block in blocks)
        assert any('✅ Verified' in str(block) for block in blocks)
        assert any('Score: 100' in str(block) for block in blocks)
        assert any('Confidence' in str(block) for block in blocks)
    
    def test_create_article_blocks_not_verified(self, notifier):
        """未検証記事のブロック作成を確認"""
        article = {
            'title': 'Unverified Article',
            'url': 'https://example.com/unverified',
            'score': 50,
            'verification': {
                'verified': False,
                'related_count': 0,
                'dev_to_count': 0,
                'medium_count': 0,
                'confidence_score': 0.0
            }
        }
        
        blocks = notifier._create_article_blocks(article)
        
        assert any('❌ Not Verified' in str(block) for block in blocks)
        assert any('0 related articles found' in str(block) for block in blocks)
    
    @responses.activate
    def test_send_error_notification_success(self, notifier):
        """エラー通知の送信が成功することを確認"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=200
        )
        
        result = notifier.send_error_notification("Test error message")
        
        assert result is True
        assert len(responses.calls) == 1
        
        request_body = responses.calls[0].request.body
        assert b'AI News Feeder Error' in request_body
        assert b'Test error message' in request_body
    
    @responses.activate
    def test_send_error_notification_failure(self, notifier):
        """エラー通知送信失敗時の処理を確認"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=500
        )
        
        result = notifier.send_error_notification("Test error")
        assert result is False
    
    def test_webhook_url_from_config(self, notifier):
        """Webhook URLが設定から取得されることを確認"""
        assert notifier.webhook_url == "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
    
    @patch('src.utils.slack_notifier.datetime')
    def test_timestamp_formatting(self, mock_datetime, notifier):
        """タイムスタンプのフォーマットを確認"""
        mock_now = Mock()
        mock_now.strftime.return_value = "2025/01/01 12:00"
        mock_datetime.now.return_value = mock_now
        
        article = {
            'title': 'Test',
            'url': 'https://example.com',
            'score': 100,
            'verification': {'verified': True, 'related_count': 1, 'dev_to_count': 1, 'medium_count': 0}
        }
        
        blocks = notifier._create_article_blocks(article)
        
        # 日時フォーマットが含まれていることを確認
        assert any('2025/01/01 12:00' in str(block) for block in blocks)
    
    def test_get_confidence_level(self, notifier):
        """信頼度レベル判定のテスト"""
        assert notifier._get_confidence_level(0.9) == "🟢 High"
        assert notifier._get_confidence_level(0.8) == "🟢 High"
        assert notifier._get_confidence_level(0.7) == "🟡 Medium"
        assert notifier._get_confidence_level(0.5) == "🟡 Medium"
        assert notifier._get_confidence_level(0.4) == "🔴 Low"
        assert notifier._get_confidence_level(0.0) == "🔴 Low"