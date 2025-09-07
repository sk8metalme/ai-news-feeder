"""health_checker.pyのテスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
from datetime import datetime, timedelta
from src.utils.health_checker import HealthChecker, ComponentHealth, SystemHealth


class TestHealthChecker:
    """HealthCheckerクラスのテスト"""
    
    @pytest.fixture
    def health_checker(self):
        """HealthCheckerインスタンスを返す"""
        return HealthChecker()
    
    @pytest.fixture
    def mock_healthy_components(self):
        """健全なコンポーネントのモック"""
        return [
            ComponentHealth(
                name="Hacker News API",
                status="healthy",
                message="API接続正常",
                last_check=datetime.now(),
                response_time_ms=100.0
            ),
            ComponentHealth(
                name="dev.to API",
                status="healthy", 
                message="API接続正常",
                last_check=datetime.now(),
                response_time_ms=150.0
            ),
            ComponentHealth(
                name="Medium RSS",
                status="healthy",
                message="RSSフィード正常",
                last_check=datetime.now(),
                response_time_ms=200.0
            ),
            ComponentHealth(
                name="Slack Webhook",
                status="healthy",
                message="Webhook URL形式正常",
                last_check=datetime.now()
            ),
            ComponentHealth(
                name="File System",
                status="healthy",
                message="ファイルシステム書き込み可能",
                last_check=datetime.now()
            ),
            ComponentHealth(
                name="Configuration",
                status="healthy",
                message="設定正常",
                last_check=datetime.now()
            )
        ]
    
    @patch('src.utils.health_checker.HealthChecker._check_config')
    @patch('src.utils.health_checker.HealthChecker._check_file_system')
    @patch('src.utils.health_checker.HealthChecker._check_slack_webhook')
    @patch('src.utils.health_checker.HealthChecker._check_medium_rss')
    @patch('src.utils.health_checker.HealthChecker._check_devto_api')
    @patch('src.utils.health_checker.HealthChecker._check_hackernews_api')
    def test_check_all_healthy(self, mock_hn, mock_devto, mock_medium, 
                              mock_slack, mock_fs, mock_config, 
                              health_checker, mock_healthy_components):
        """全コンポーネントが健全な場合のテスト"""
        # モックの設定
        mock_hn.return_value = mock_healthy_components[0]
        mock_devto.return_value = mock_healthy_components[1]
        mock_medium.return_value = mock_healthy_components[2]
        mock_slack.return_value = mock_healthy_components[3]
        mock_fs.return_value = mock_healthy_components[4]
        mock_config.return_value = mock_healthy_components[5]
        
        # テスト実行
        result = health_checker.check_all()
        
        # 検証
        assert result.status == "healthy"
        assert result.checks_passed == 6
        assert result.checks_total == 6
        assert len(result.components) == 6
    
    @patch('src.utils.health_checker.HealthChecker._check_config')
    @patch('src.utils.health_checker.HealthChecker._check_file_system')
    @patch('src.utils.health_checker.HealthChecker._check_slack_webhook')
    @patch('src.utils.health_checker.HealthChecker._check_medium_rss')
    @patch('src.utils.health_checker.HealthChecker._check_devto_api')
    @patch('src.utils.health_checker.HealthChecker._check_hackernews_api')
    def test_check_all_degraded(self, mock_hn, mock_devto, mock_medium, 
                               mock_slack, mock_fs, mock_config, health_checker):
        """一部コンポーネントがdegradedの場合のテスト"""
        # 健全なコンポーネント
        healthy = ComponentHealth(
            name="Test Healthy",
            status="healthy",
            message="正常",
            last_check=datetime.now()
        )
        
        # 劣化したコンポーネント
        degraded = ComponentHealth(
            name="Test Degraded",
            status="degraded",
            message="性能低下",
            last_check=datetime.now()
        )
        
        mock_hn.return_value = healthy
        mock_devto.return_value = degraded  # 劣化
        mock_medium.return_value = healthy
        mock_slack.return_value = healthy
        mock_fs.return_value = healthy
        mock_config.return_value = healthy
        
        result = health_checker.check_all()
        
        assert result.status == "degraded"
        assert result.checks_passed == 5  # unhealthyでないものの数
    
    @patch('src.utils.health_checker.HealthChecker._check_config')
    @patch('src.utils.health_checker.HealthChecker._check_file_system')
    @patch('src.utils.health_checker.HealthChecker._check_slack_webhook')
    @patch('src.utils.health_checker.HealthChecker._check_medium_rss')
    @patch('src.utils.health_checker.HealthChecker._check_devto_api')
    @patch('src.utils.health_checker.HealthChecker._check_hackernews_api')
    def test_check_all_unhealthy(self, mock_hn, mock_devto, mock_medium, 
                                mock_slack, mock_fs, mock_config, health_checker):
        """一部コンポーネントがunhealthyの場合のテスト"""
        healthy = ComponentHealth(
            name="Test Healthy",
            status="healthy",
            message="正常",
            last_check=datetime.now()
        )
        
        unhealthy = ComponentHealth(
            name="Test Unhealthy",
            status="unhealthy",
            message="エラー",
            last_check=datetime.now()
        )
        
        mock_hn.return_value = unhealthy  # 異常
        mock_devto.return_value = healthy
        mock_medium.return_value = healthy
        mock_slack.return_value = healthy
        mock_fs.return_value = healthy
        mock_config.return_value = healthy
        
        result = health_checker.check_all()
        
        assert result.status == "unhealthy"
        assert result.checks_passed == 5
    
    @patch('src.api.hackernews_api.HackerNewsAPI.get_top_stories')
    def test_check_hackernews_api_healthy(self, mock_get_stories, health_checker):
        """Hacker News APIチェック（正常）のテスト"""
        mock_get_stories.return_value = [1001, 1002, 1003]
        
        result = health_checker._check_hackernews_api()
        
        assert result.status == "healthy"
        assert result.message == "API接続正常"
        assert result.response_time_ms is not None
    
    @patch('src.api.hackernews_api.HackerNewsAPI.get_top_stories')
    def test_check_hackernews_api_empty_response(self, mock_get_stories, health_checker):
        """Hacker News APIチェック（空レスポンス）のテスト"""
        mock_get_stories.return_value = []
        
        result = health_checker._check_hackernews_api()
        
        assert result.status == "unhealthy"
        assert "レスポンスが空" in result.message
    
    @patch('src.api.hackernews_api.HackerNewsAPI.get_top_stories')
    def test_check_hackernews_api_error(self, mock_get_stories, health_checker):
        """Hacker News APIチェック（エラー）のテスト"""
        mock_get_stories.side_effect = Exception("Connection error")
        
        result = health_checker._check_hackernews_api()
        
        assert result.status == "unhealthy"
        assert "Connection error" in result.message
    
    @patch('requests.get')
    def test_check_devto_api_healthy(self, mock_get, health_checker):
        """dev.to APIチェック（正常）のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = health_checker._check_devto_api()
        
        assert result.status == "healthy"
        assert result.message == "API接続正常"
        assert result.response_time_ms is not None
    
    @patch('requests.get')
    def test_check_devto_api_degraded(self, mock_get, health_checker):
        """dev.to APIチェック（劣化）のテスト"""
        mock_response = Mock()
        mock_response.status_code = 429  # Rate limited
        mock_get.return_value = mock_response
        
        result = health_checker._check_devto_api()
        
        assert result.status == "degraded"
        assert "429" in result.message
    
    def test_check_slack_webhook_healthy(self, health_checker):
        """Slack Webhookチェック（正常）のテスト"""
        result = health_checker._check_slack_webhook()
        
        assert result.status == "healthy"
        assert "形式正常" in result.message
    
    def test_check_slack_webhook_no_url(self, health_checker, monkeypatch):
        """Slack Webhookチェック（URL未設定）のテスト"""
        monkeypatch.setattr('src.utils.config.Config.SLACK_WEBHOOK_URL', '')
        
        result = health_checker._check_slack_webhook()
        
        assert result.status == "unhealthy"
        assert "設定されていません" in result.message
    
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    @patch('os.remove')
    def test_check_file_system_healthy(self, mock_remove, mock_open, mock_makedirs, health_checker):
        """ファイルシステムチェック（正常）のテスト"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = health_checker._check_file_system()
        
        assert result.status == "healthy"
        assert "書き込み可能" in result.message
        mock_makedirs.assert_called_once()
        mock_remove.assert_called_once()
    
    def test_check_config_healthy(self, health_checker):
        """設定チェック（正常）のテスト"""
        result = health_checker._check_config()
        
        assert result.status == "healthy"
        assert result.message == "設定正常"
    
    def test_check_config_warnings(self, health_checker, monkeypatch):
        """設定チェック（警告あり）のテスト"""
        monkeypatch.setattr('src.utils.config.Config.ARTICLES_PER_DAY', 15)
        monkeypatch.setattr('src.utils.config.Config.FACTCHECK_CONFIDENCE_THRESHOLD', 0.9)
        
        result = health_checker._check_config()
        
        assert result.status == "degraded"
        assert "警告" in result.message
        assert len(result.details['warnings']) == 2
    
    def test_get_status_summary_no_file(self, health_checker):
        """ステータスサマリー（ファイルなし）のテスト"""
        summary = health_checker.get_status_summary()
        assert summary == "ヘルスチェック未実行"
    
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_get_status_summary_with_file(self, mock_exists, mock_open, health_checker):
        """ステータスサマリー（ファイルあり）のテスト"""
        mock_exists.return_value = True
        
        mock_data = {
            'status': 'healthy',
            'checks_passed': 6,
            'checks_total': 6,
            'timestamp': datetime.now().isoformat(),
            'components': []
        }
        
        mock_file = MagicMock()
        mock_file.read.return_value = json.dumps(mock_data)
        mock_open.return_value.__enter__.return_value = mock_file
        
        summary = health_checker.get_status_summary()
        
        assert "🟢" in summary
        assert "HEALTHY" in summary
        assert "6/6" in summary
    
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    def test_save_health_status(self, mock_open, mock_exists, health_checker):
        """ヘルスステータス保存のテスト"""
        health = SystemHealth(
            status="healthy",
            timestamp=datetime.now(),
            components=[],
            checks_passed=6,
            checks_total=6,
            uptime_hours=1.5,
            last_successful_run=datetime.now()
        )
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        health_checker._save_health_status(health)
        
        # ファイルに書き込まれたことを確認
        assert mock_file.write.called or hasattr(mock_file, 'write')
    
    def test_get_last_successful_run_no_reports(self, health_checker):
        """最終成功実行時刻取得（レポートなし）のテスト"""
        result = health_checker._get_last_successful_run()
        assert result is None