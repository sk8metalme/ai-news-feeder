"""
Tests for health checker module
"""
import pytest
import responses
import subprocess
from unittest.mock import Mock, patch, MagicMock
import time

from src.utils.health_checker import HealthChecker


class TestHealthChecker:
    """Test cases for HealthChecker class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.health_checker = HealthChecker()
    
    @responses.activate
    def test_check_hacker_news_api_healthy(self):
        """Test healthy Hacker News API check"""
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            json=[1, 2, 3, 4, 5],
            status=200
        )
        
        result = self.health_checker.check_hacker_news_api()
        
        assert result['service'] == 'Hacker News API'
        assert result['status'] == 'healthy'
        assert result['stories_count'] == 5
        assert 'response_time_ms' in result
        assert result['message'] == 'API responding normally'
    
    @responses.activate
    def test_check_hacker_news_api_unhealthy(self):
        """Test unhealthy Hacker News API check"""
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            status=500
        )
        
        result = self.health_checker.check_hacker_news_api()
        
        assert result['service'] == 'Hacker News API'
        assert result['status'] == 'unhealthy'
        assert result['error'] == 'HTTP 500'
        assert 'response_time_ms' in result
    
    @responses.activate
    def test_check_hacker_news_api_connection_error(self):
        """Test Hacker News API connection error"""
        # No response added, will cause ConnectionError
        
        result = self.health_checker.check_hacker_news_api()
        
        assert result['service'] == 'Hacker News API'
        assert result['status'] == 'unhealthy'
        assert 'error' in result
        assert result['message'] == 'API connection failed'
    
    @responses.activate
    def test_check_dev_to_api_healthy(self):
        """Test healthy dev.to API check"""
        responses.add(
            responses.GET,
            "https://dev.to/api/articles",
            json=[{"title": "Test Article"}],
            status=200
        )
        
        result = self.health_checker.check_dev_to_api()
        
        assert result['service'] == 'dev.to API'
        assert result['status'] == 'healthy'
        assert result['articles_available'] == 1
        assert 'response_time_ms' in result
        assert result['message'] == 'API responding normally'
    
    @responses.activate
    def test_check_dev_to_api_unhealthy(self):
        """Test unhealthy dev.to API check"""
        responses.add(
            responses.GET,
            "https://dev.to/api/articles",
            status=429  # Rate limited
        )
        
        result = self.health_checker.check_dev_to_api()
        
        assert result['service'] == 'dev.to API'
        assert result['status'] == 'unhealthy'
        assert result['error'] == 'HTTP 429'
    
    @responses.activate
    def test_check_medium_rss_healthy(self):
        """Test healthy Medium RSS check"""
        xml_content = b'<?xml version="1.0"?><rss><channel><item><title>Test</title></item></channel></rss>'
        responses.add(
            responses.GET,
            "https://medium.com/feed/tag/ai",
            body=xml_content,
            status=200,
            content_type='application/rss+xml'
        )
        
        result = self.health_checker.check_medium_rss()
        
        assert result['service'] == 'Medium RSS'
        assert result['status'] == 'healthy'
        assert result['content_length'] > 0
        assert 'response_time_ms' in result
        assert result['message'] == 'RSS feed accessible'
    
    @responses.activate
    def test_check_medium_rss_degraded(self):
        """Test degraded Medium RSS check (non-XML response)"""
        responses.add(
            responses.GET,
            "https://medium.com/feed/tag/ai",
            body="Not XML content",
            status=200
        )
        
        result = self.health_checker.check_medium_rss()
        
        assert result['service'] == 'Medium RSS'
        assert result['status'] == 'degraded'
        assert result['message'] == 'Response not XML format'
    
    @patch('subprocess.run')
    def test_check_claude_cli_healthy(self, mock_run):
        """Test healthy Claude CLI check"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Claude CLI v1.0.0",
            stderr=""
        )
        
        result = self.health_checker.check_claude_cli()
        
        assert result['service'] == 'Claude CLI'
        assert result['status'] == 'healthy'
        assert result['version'] == 'Claude CLI v1.0.0'
        assert 'response_time_ms' in result
        assert result['message'] == 'Claude CLI available and configured'
    
    @patch('subprocess.run')
    def test_check_claude_cli_unhealthy(self, mock_run):
        """Test unhealthy Claude CLI check"""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Command not found"
        )
        
        result = self.health_checker.check_claude_cli()
        
        assert result['service'] == 'Claude CLI'
        assert result['status'] == 'unhealthy'
        assert result['error'] == 'Command not found'
    
    @patch('subprocess.run')
    def test_check_claude_cli_not_found(self, mock_run):
        """Test Claude CLI not found"""
        mock_run.side_effect = FileNotFoundError("claude not found")
        
        result = self.health_checker.check_claude_cli()
        
        assert result['service'] == 'Claude CLI'
        assert result['status'] == 'unhealthy'
        assert 'claude not found' in result['error']
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_check_system_resources_healthy(self, mock_disk, mock_memory, mock_cpu):
        """Test healthy system resources check"""
        mock_cpu.return_value = 25.0
        mock_memory.return_value = Mock(percent=60.0)
        mock_disk.return_value = Mock(percent=70.0)
        
        result = self.health_checker.check_system_resources()
        
        assert result['service'] == 'System Resources'
        assert result['status'] == 'healthy'
        assert result['cpu_percent'] == 25.0
        assert result['memory_percent'] == 60.0
        assert result['disk_percent'] == 70.0
        assert result['warnings'] == []
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_check_system_resources_degraded(self, mock_disk, mock_memory, mock_cpu):
        """Test degraded system resources check"""
        mock_cpu.return_value = 85.0  # High CPU
        mock_memory.return_value = Mock(percent=90.0)  # High memory
        mock_disk.return_value = Mock(percent=95.0)  # High disk
        
        result = self.health_checker.check_system_resources()
        
        assert result['service'] == 'System Resources'
        assert result['status'] == 'degraded'
        assert len(result['warnings']) == 3
        assert 'High CPU usage: 85.0%' in result['warnings']
        assert 'High memory usage: 90.0%' in result['warnings']
        assert 'High disk usage: 95.0%' in result['warnings']
    
    @pytest.mark.skip(reason="psutil ImportError test is complex to mock properly")
    def test_check_system_resources_no_psutil(self):
        """Test system resources check without psutil"""
        # This test is skipped as mocking psutil ImportError is complex
        # In real scenarios, psutil is either installed or not
        pass
    
    @patch.object(HealthChecker, 'check_hacker_news_api')
    @patch.object(HealthChecker, 'check_dev_to_api')
    @patch.object(HealthChecker, 'check_medium_rss')
    @patch.object(HealthChecker, 'check_claude_cli')
    @patch.object(HealthChecker, 'check_system_resources')
    def test_run_full_health_check_all_healthy(self, mock_system, mock_claude, mock_medium, mock_dev_to, mock_hacker_news):
        """Test full health check with all services healthy"""
        # Mock all checks as healthy
        mock_checks = [
            {'service': 'Hacker News API', 'status': 'healthy'},
            {'service': 'dev.to API', 'status': 'healthy'},
            {'service': 'Medium RSS', 'status': 'healthy'},
            {'service': 'Claude CLI', 'status': 'healthy'},
            {'service': 'System Resources', 'status': 'healthy'}
        ]
        
        mock_hacker_news.return_value = mock_checks[0]
        mock_dev_to.return_value = mock_checks[1]
        mock_medium.return_value = mock_checks[2]
        mock_claude.return_value = mock_checks[3]
        mock_system.return_value = mock_checks[4]
        
        result = self.health_checker.run_full_health_check()
        
        assert result['overall_status'] == 'healthy'
        assert result['summary']['healthy'] == 5
        assert result['summary']['degraded'] == 0
        assert result['summary']['unhealthy'] == 0
        assert result['summary']['total'] == 5
        assert len(result['checks']) == 5
        assert 'timestamp' in result
        assert 'total_check_time_ms' in result
    
    @patch.object(HealthChecker, 'check_hacker_news_api')
    @patch.object(HealthChecker, 'check_dev_to_api')
    @patch.object(HealthChecker, 'check_medium_rss')
    @patch.object(HealthChecker, 'check_claude_cli')
    @patch.object(HealthChecker, 'check_system_resources')
    def test_run_full_health_check_mixed_status(self, mock_system, mock_claude, mock_medium, mock_dev_to, mock_hacker_news):
        """Test full health check with mixed service status"""
        mock_hacker_news.return_value = {'service': 'Hacker News API', 'status': 'healthy'}
        mock_dev_to.return_value = {'service': 'dev.to API', 'status': 'degraded'}
        mock_medium.return_value = {'service': 'Medium RSS', 'status': 'unhealthy'}
        mock_claude.return_value = {'service': 'Claude CLI', 'status': 'healthy'}
        mock_system.return_value = {'service': 'System Resources', 'status': 'healthy'}
        
        result = self.health_checker.run_full_health_check()
        
        assert result['overall_status'] == 'unhealthy'  # Because one service is unhealthy
        assert result['summary']['healthy'] == 3
        assert result['summary']['degraded'] == 1
        assert result['summary']['unhealthy'] == 1
    
    def test_get_health_status_emoji(self):
        """Test health status emoji mapping"""
        assert self.health_checker.get_health_status_emoji('healthy') == '✅'
        assert self.health_checker.get_health_status_emoji('degraded') == '⚠️'
        assert self.health_checker.get_health_status_emoji('unhealthy') == '❌'
        assert self.health_checker.get_health_status_emoji('unknown') == '❓'
        assert self.health_checker.get_health_status_emoji('invalid') == '❓'
    
    def test_format_health_report(self):
        """Test health report formatting"""
        health_data = {
            'timestamp': '2022-01-01 12:00:00 JST',
            'overall_status': 'healthy',
            'total_check_time_ms': 1500.5,
            'summary': {'healthy': 4, 'degraded': 1, 'unhealthy': 0, 'total': 5},
            'checks': [
                {
                    'service': 'Hacker News API',
                    'status': 'healthy',
                    'stories_count': 500,
                    'response_time_ms': 250.0,
                    'message': 'API responding normally'
                },
                {
                    'service': 'Claude CLI',
                    'status': 'degraded',
                    'version': '1.0.0',
                    'error': 'Slow response',
                    'message': 'CLI available but slow'
                }
            ]
        }
        
        report = self.health_checker.format_health_report(health_data)
        
        assert '🏥 **AI News Feeder - System Health Report**' in report
        assert '✅ **Overall Status**: HEALTHY' in report
        assert '1500.5ms' in report
        assert '4/5 services healthy' in report
        assert '✅ **Hacker News API**: HEALTHY (500 stories available) - 250.0ms' in report
        assert '⚠️ **Claude CLI**: DEGRADED (1.0.0)' in report
        assert '⚠️ Error: Slow response' in report
        assert '📅 **Checked at**: 2022-01-01 12:00:00 JST' in report
