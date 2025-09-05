"""
Tests for scheduler module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.scheduler import AINewsScheduler


class TestAINewsScheduler:
    """Test cases for AINewsScheduler class"""
    
    def setup_method(self):
        """Setup test instance with mocked dependencies"""
        with patch('src.scheduler.HackerNewsAPI'), \
             patch('src.scheduler.FactChecker'), \
             patch('src.scheduler.SlackNotifier'), \
             patch('src.scheduler.ReportGenerator'):
            self.scheduler = AINewsScheduler()
    
    @patch('src.scheduler.time.sleep')
    def test_run_verification_job_success(self, mock_sleep, sample_hn_story, sample_verification_result):
        """Test successful verification job execution"""
        # Mock dependencies
        self.scheduler.hn_api.get_ai_stories.return_value = [sample_hn_story]
        self.scheduler.fact_checker.verify_article.return_value = sample_verification_result
        self.scheduler.slack_notifier.send_verification_report.return_value = True
        self.scheduler.slack_notifier.send_daily_summary.return_value = True
        self.scheduler.report_generator.save_daily_report.return_value = "/path/to/report.json"
        self.scheduler.report_generator.generate_summary_stats.return_value = {
            "total_articles": 1,
            "verified_articles": 1,
            "verification_rate": 100.0
        }
        
        # Run the job
        self.scheduler.run_verification_job()
        
        # Verify method calls
        self.scheduler.hn_api.get_ai_stories.assert_called_once()
        self.scheduler.fact_checker.verify_article.assert_called_once()
        self.scheduler.slack_notifier.send_verification_report.assert_called_once()
        self.scheduler.slack_notifier.send_daily_summary.assert_called_once()
        self.scheduler.report_generator.save_daily_report.assert_called_once()
    
    def test_run_verification_job_no_stories(self):
        """Test verification job with no AI stories found"""
        # Mock no stories found
        self.scheduler.hn_api.get_ai_stories.return_value = []
        
        # Run the job
        self.scheduler.run_verification_job()
        
        # Verify only the first method was called
        self.scheduler.hn_api.get_ai_stories.assert_called_once()
        self.scheduler.fact_checker.verify_article.assert_not_called()
        self.scheduler.slack_notifier.send_verification_report.assert_not_called()
    
    @patch('src.scheduler.time.sleep')
    def test_run_verification_job_unverified_articles(self, mock_sleep, sample_hn_story):
        """Test verification job with unverified articles"""
        unverified_result = {
            "verification_status": "unverified",
            "total_related_count": 0
        }
        
        # Mock dependencies
        self.scheduler.hn_api.get_ai_stories.return_value = [sample_hn_story]
        self.scheduler.fact_checker.verify_article.return_value = unverified_result
        self.scheduler.slack_notifier.send_daily_summary.return_value = True
        self.scheduler.report_generator.save_daily_report.return_value = "/path/to/report.json"
        self.scheduler.report_generator.generate_summary_stats.return_value = {
            "total_articles": 1,
            "verified_articles": 0,
            "verification_rate": 0.0
        }
        
        # Run the job
        self.scheduler.run_verification_job()
        
        # Verify verification report is NOT sent for unverified articles
        self.scheduler.slack_notifier.send_verification_report.assert_not_called()
        # But daily summary should still be sent
        self.scheduler.slack_notifier.send_daily_summary.assert_called_once()
    
    def test_run_verification_job_exception_handling(self):
        """Test verification job exception handling"""
        # Mock an exception during story fetching
        self.scheduler.hn_api.get_ai_stories.side_effect = Exception("API Error")
        self.scheduler.slack_notifier.send_notification.return_value = True
        
        # Run the job (should not raise exception)
        self.scheduler.run_verification_job()
        
        # Verify error notification was sent
        self.scheduler.slack_notifier.send_notification.assert_called_once()
        call_args = self.scheduler.slack_notifier.send_notification.call_args[0]
        assert "🚨 AI News Bot Error" in call_args[0]
        assert "API Error" in call_args[0]
    
    @patch('src.scheduler.schedule')
    def test_start_scheduler_setup(self, mock_schedule):
        """Test scheduler setup"""
        # Mock schedule chain
        mock_schedule.every.return_value.day = Mock()
        mock_schedule.every.return_value.day.at.return_value.do = Mock()
        
        # Mock the run_verification_job to avoid actual execution
        with patch.object(self.scheduler, 'run_verification_job'):
            # Mock the infinite loop to exit immediately
            with patch('src.scheduler.schedule.run_pending'), \
                 patch('src.scheduler.time.sleep', side_effect=KeyboardInterrupt):
                
                try:
                    self.scheduler.start_scheduler()
                except KeyboardInterrupt:
                    pass
        
        # Verify schedule was configured
        mock_schedule.every.return_value.day.at.assert_called_with("09:00")


class TestSchedulerIntegration:
    """Integration tests for scheduler with real dependencies"""
    
    @patch('src.scheduler.time.sleep')
    @patch('src.api.hacker_news.requests.get')
    @patch('src.verification.fact_checker.requests.Session.get')
    @patch('src.notification.slack_notifier.requests.post')
    def test_full_workflow_integration(self, mock_slack_post, mock_fact_get, mock_hn_get, mock_sleep, tmp_path):
        """Test complete workflow integration"""
        # Mock Hacker News API responses
        mock_hn_get.side_effect = [
            # Top stories response
            Mock(json=lambda: [1, 2, 3], status_code=200),
            # Story details responses
            Mock(json=lambda: {
                "id": 1,
                "title": "ChatGPT-4 AI Breakthrough",
                "url": "https://example.com/chatgpt4",
                "score": 100,
                "time": int(datetime.now().timestamp())
            }, status_code=200),
            Mock(json=lambda: {
                "id": 2,
                "title": "Non-AI News",
                "url": "https://example.com/other",
                "score": 50,
                "time": int(datetime.now().timestamp())
            }, status_code=200),
        ]
        
        # Mock fact checker responses
        mock_fact_get.side_effect = [
            # dev.to API response
            Mock(json=lambda: [
                {
                    "title": "Related ChatGPT Article",
                    "url": "https://dev.to/article1",
                    "description": "About ChatGPT",
                    "tag_list": ["ai", "chatgpt"],
                    "published_at": "2022-01-01T00:00:00Z"
                }
            ], status_code=200),
            # Medium RSS responses (one for each tag)
            Mock(content=b'<?xml version="1.0"?><rss><channel><item><title>ChatGPT Guide</title><link>https://medium.com/article1</link></item></channel></rss>', status_code=200),
            Mock(content=b'<?xml version="1.0"?><rss><channel></channel></rss>', status_code=200),
            Mock(content=b'<?xml version="1.0"?><rss><channel></channel></rss>', status_code=200),
            Mock(content=b'<?xml version="1.0"?><rss><channel></channel></rss>', status_code=200),
        ]
        
        # Mock Slack responses
        mock_slack_post.return_value = Mock(status_code=200)
        
        # Create scheduler with temporary data directory and mock webhook URL
        with patch('config.settings.DATA_DIR', str(tmp_path)), \
             patch('src.notification.slack_notifier.SLACK_WEBHOOK_URL', 'https://hooks.slack.com/test'):
            scheduler = AINewsScheduler()
            scheduler.slack_notifier.webhook_url = 'https://hooks.slack.com/test'  # Directly set webhook URL
            scheduler.run_verification_job()
        
        # Verify Slack notifications were sent
        assert mock_slack_post.call_count >= 1  # At least verification report or summary
