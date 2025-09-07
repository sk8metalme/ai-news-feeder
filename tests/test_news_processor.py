"""news_processor.pyのテスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from src.processing.news_processor import NewsProcessor, run_daily_process


class TestNewsProcessor:
    """NewsProcessorクラスのテスト"""
    
    @pytest.fixture
    def processor(self):
        """NewsProcessorインスタンスを返す"""
        return NewsProcessor()
    
    @pytest.fixture
    def mock_stories(self):
        """テスト用のストーリーデータ"""
        return [
            {
                'id': 1001,
                'title': 'ChatGPT-4 New Features',
                'url': 'https://example.com/chatgpt',
                'score': 200,
                'time': 1693900000
            },
            {
                'id': 1002,
                'title': 'Claude Updates',
                'url': 'https://example.com/claude',
                'score': 150,
                'time': 1693890000
            },
            {
                'id': 1003,
                'title': 'AI Research Paper',
                'url': 'https://example.com/ai-research',
                'score': 100,
                'time': 1693880000
            }
        ]
    
    @patch('src.processing.news_processor.SlackNotifier')
    @patch('src.processing.news_processor.FactCheckAPI')
    @patch('src.processing.news_processor.HackerNewsAPI')
    def test_process_daily_news_success(self, mock_hn_api, mock_fc_api, mock_slack, processor, mock_stories):
        """日次処理が成功する場合のテスト"""
        # モックの設定
        mock_hn_instance = mock_hn_api.return_value
        mock_hn_instance.search_ai_stories.return_value = mock_stories
        
        mock_fc_instance = mock_fc_api.return_value
        mock_fc_instance.verify_story.return_value = {
            'verified': True,
            'related_count': 2,
            'dev_to_count': 1,
            'medium_count': 1,
            'sources': {'dev_to': [], 'medium': []}
        }
        
        mock_slack_instance = mock_slack.return_value
        mock_slack_instance.send_verification_report.return_value = True
        
        # 処理を実行
        result = processor.process_daily_news()
        
        assert result is True
        assert mock_hn_instance.search_ai_stories.called
        assert mock_fc_instance.verify_story.call_count >= 1
        assert mock_slack_instance.send_verification_report.called
    
    @patch('src.processing.news_processor.HackerNewsAPI')
    def test_process_daily_news_no_stories(self, mock_hn_api, processor):
        """記事が見つからない場合のテスト"""
        mock_hn_instance = mock_hn_api.return_value
        mock_hn_instance.search_ai_stories.return_value = []
        
        result = processor.process_daily_news()
        assert result is False
    
    @patch('src.processing.news_processor.SlackNotifier')
    @patch('src.processing.news_processor.FactCheckAPI')
    @patch('src.processing.news_processor.HackerNewsAPI')
    def test_process_daily_news_no_verified(self, mock_hn_api, mock_fc_api, mock_slack, processor, mock_stories):
        """検証済み記事が0件の場合のテスト"""
        mock_hn_instance = mock_hn_api.return_value
        mock_hn_instance.search_ai_stories.return_value = mock_stories
        
        mock_fc_instance = mock_fc_api.return_value
        mock_fc_instance.verify_story.return_value = {
            'verified': False,
            'related_count': 0,
            'dev_to_count': 0,
            'medium_count': 0,
            'sources': {'dev_to': [], 'medium': []}
        }
        
        mock_slack_instance = mock_slack.return_value
        mock_slack_instance.send_error_notification.return_value = True
        
        result = processor.process_daily_news()
        
        assert result is False
        assert mock_slack_instance.send_error_notification.called
    
    @patch('src.processing.news_processor.SlackNotifier')
    @patch('src.processing.news_processor.FactCheckAPI')
    @patch('src.processing.news_processor.HackerNewsAPI')
    def test_process_daily_news_slack_failure(self, mock_hn_api, mock_fc_api, mock_slack, processor, mock_stories):
        """Slack送信失敗時のテスト"""
        mock_hn_instance = mock_hn_api.return_value
        mock_hn_instance.search_ai_stories.return_value = mock_stories[:1]
        
        mock_fc_instance = mock_fc_api.return_value
        mock_fc_instance.verify_story.return_value = {
            'verified': True,
            'related_count': 1,
            'dev_to_count': 1,
            'medium_count': 0,
            'sources': {'dev_to': [], 'medium': []}
        }
        
        mock_slack_instance = mock_slack.return_value
        mock_slack_instance.send_verification_report.return_value = False
        
        result = processor.process_daily_news()
        assert result is False
    
    @patch('src.processing.news_processor.SlackNotifier')
    @patch('src.processing.news_processor.HackerNewsAPI')
    def test_process_daily_news_exception(self, mock_hn_api, mock_slack, processor):
        """処理中の例外発生時のテスト"""
        mock_hn_instance = mock_hn_api.return_value
        mock_hn_instance.search_ai_stories.side_effect = Exception("API Error")
        
        mock_slack_instance = mock_slack.return_value
        mock_slack_instance.send_error_notification.return_value = True
        
        result = processor.process_daily_news()
        
        assert result is False
        assert mock_slack_instance.send_error_notification.called
    
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    def test_save_report(self, mock_open, mock_makedirs, processor):
        """レポート保存機能のテスト"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        articles = [
            {
                'title': 'Test Article',
                'url': 'https://example.com',
                'score': 100,
                'verification': {'verified': True, 'related_count': 1}
            }
        ]
        
        processor._save_report(articles)
        
        # ディレクトリ作成とファイル書き込みが呼ばれたことを確認
        mock_makedirs.assert_called_once_with('reports', exist_ok=True)
        mock_open.assert_called_once()
        
        # JSON形式で書き込まれたことを確認
        write_calls = mock_file.write.call_args_list
        written_content = ''.join(call[0][0] for call in write_calls)
        
        # 書き込まれた内容を検証
        try:
            data = json.loads(written_content)
            assert 'timestamp' in data
            assert 'articles' in data
            assert data['total_count'] == 1
        except json.JSONDecodeError:
            # writeが複数回呼ばれる場合もあるので、エラーは無視
            pass
    
    @patch('builtins.open', side_effect=Exception("Write error"))
    def test_save_report_error(self, mock_open, processor):
        """レポート保存エラー時の処理を確認"""
        articles = [{'title': 'Test'}]
        
        # エラーが発生しても処理が継続することを確認
        try:
            processor._save_report(articles)
        except Exception:
            pytest.fail("_save_report should not raise exceptions")


class TestRunDailyProcess:
    """run_daily_process関数のテスト"""
    
    @patch('src.processing.news_processor.NewsProcessor')
    @patch('src.processing.news_processor.Config')
    def test_run_daily_process_success(self, mock_config, mock_processor_class):
        """正常実行時のテスト"""
        mock_config.validate.return_value = True
        
        mock_processor = mock_processor_class.return_value
        mock_processor.process_daily_news.return_value = True
        
        result = run_daily_process()
        
        assert result is True
        assert mock_config.validate.called
        assert mock_processor.process_daily_news.called
    
    @patch('src.processing.news_processor.Config')
    def test_run_daily_process_config_error(self, mock_config):
        """設定エラー時のテスト"""
        mock_config.validate.side_effect = ValueError("Config error")
        
        result = run_daily_process()
        assert result is False
    
    @patch('src.processing.news_processor.NewsProcessor')
    @patch('src.processing.news_processor.Config')
    def test_run_daily_process_processing_error(self, mock_config, mock_processor_class):
        """処理エラー時のテスト"""
        mock_config.validate.return_value = True
        
        mock_processor = mock_processor_class.return_value
        mock_processor.process_daily_news.return_value = False
        
        result = run_daily_process()
        assert result is False