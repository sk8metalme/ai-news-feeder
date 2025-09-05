"""
Tests for Slack notifier module
"""
import pytest
import responses
import json
from unittest.mock import Mock, patch

from src.notification.slack_notifier import SlackNotifier


class TestSlackNotifier:
    """Test cases for SlackNotifier class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
        self.notifier = SlackNotifier(webhook_url=self.webhook_url)
    
    def test_format_verification_report(self, sample_verification_result):
        """Test formatting of verification report"""
        result = self.notifier.format_verification_report(sample_verification_result)
        
        # Check that all expected elements are in the formatted message
        assert "📊 AI News Verification Report" in result
        assert "New AI Model Breakthrough: ChatGPT-5 Released" in result
        assert "✅" in result  # Verified status emoji
        assert "2 related articles found" in result
        assert "dev.to(1), Medium(1)" in result
        assert "https://example.com/chatgpt5-released" in result
        assert "2022-01-01 12:00:00 JST" in result
    
    def test_format_verification_report_unverified(self):
        """Test formatting of unverified report"""
        unverified_result = {
            "article_title": "Unverified AI News",
            "article_url": "https://example.com/unverified",
            "verification_status": "unverified",
            "total_related_count": 0,
            "related_articles": {"dev_to": [], "medium": []},
            "checked_at": "2022-01-01 12:00:00 JST"
        }
        
        result = self.notifier.format_verification_report(unverified_result)
        
        assert "📊 AI News Verification Report" in result
        assert "❌" in result  # Unverified status emoji
        assert "0 related articles found" in result
        assert "dev.to(0), Medium(0)" in result
    
    @responses.activate
    def test_send_notification_success(self):
        """Test successful notification sending"""
        responses.add(
            responses.POST,
            self.webhook_url,
            status=200
        )
        
        result = self.notifier.send_notification("Test message")
        
        assert result is True
        assert len(responses.calls) == 1
        
        # Check request payload
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["text"] == "Test message"
        assert request_body["username"] == "AI News Bot"
        assert request_body["icon_emoji"] == ":robot_face:"
    
    @responses.activate
    def test_send_notification_with_custom_channel(self):
        """Test notification with custom channel"""
        responses.add(
            responses.POST,
            self.webhook_url,
            status=200
        )
        
        custom_channel = "#test-channel"
        result = self.notifier.send_notification("Test message", channel=custom_channel)
        
        assert result is True
        request_body = json.loads(responses.calls[0].request.body)
        assert request_body["channel"] == custom_channel
    
    @responses.activate
    def test_send_notification_failure(self):
        """Test notification sending failure"""
        responses.add(
            responses.POST,
            self.webhook_url,
            status=500
        )
        
        result = self.notifier.send_notification("Test message")
        assert result is False
    
    def test_send_notification_no_webhook_url(self):
        """Test notification without webhook URL"""
        notifier = SlackNotifier(webhook_url=None)
        result = notifier.send_notification("Test message")
        assert result is False
    
    @responses.activate
    def test_send_verification_report(self, sample_verification_result):
        """Test sending verification report"""
        responses.add(
            responses.POST,
            self.webhook_url,
            status=200
        )
        
        result = self.notifier.send_verification_report(sample_verification_result)
        
        assert result is True
        assert len(responses.calls) == 1
        
        # Check that the formatted message is sent
        request_body = json.loads(responses.calls[0].request.body)
        message = request_body["text"]
        assert "📊 AI News Verification Report" in message
        assert sample_verification_result["article_title"] in message
    
    @responses.activate
    def test_send_daily_summary_with_articles(self, sample_verification_result):
        """Test sending daily summary with verified articles"""
        verification_results = [
            sample_verification_result,
            {
                **sample_verification_result,
                "article_title": "Another AI Article",
                "verification_status": "unverified",
                "total_related_count": 0
            }
        ]
        
        responses.add(
            responses.POST,
            self.webhook_url,
            status=200
        )
        
        result = self.notifier.send_daily_summary(verification_results)
        
        assert result is True
        request_body = json.loads(responses.calls[0].request.body)
        message = request_body["text"]
        
        assert "📊 Daily AI News Summary" in message
        assert "**Total Articles Processed**: 2" in message
        assert "**Verified Articles**: 1" in message
        assert "**Unverified Articles**: 1" in message
        assert "New AI Model Breakthrough: ChatGPT-5 Released" in message
    
    @responses.activate
    def test_send_daily_summary_no_articles(self):
        """Test sending daily summary with no articles"""
        responses.add(
            responses.POST,
            self.webhook_url,
            status=200
        )
        
        result = self.notifier.send_daily_summary([])
        
        assert result is True
        request_body = json.loads(responses.calls[0].request.body)
        message = request_body["text"]
        
        assert "📊 Daily AI News Summary" in message
        assert "❌ No verified AI articles found today" in message
