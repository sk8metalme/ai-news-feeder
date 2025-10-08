"""
Tests for Slack notifier module
"""
import pytest
import responses
import json
from unittest.mock import Mock, patch

from src.notification.slack_notifier import SlackNotifier
from src.notification import slack_notifier as slack_mod


class TestSlackNotifier:
    """Test cases for SlackNotifier class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.webhook_url = "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
        self.notifier = SlackNotifier(webhook_url=self.webhook_url)
        # Force English UI in tests to match expectations
        slack_mod.SLACK_JA_UI = False
        # Avoid title translation (prevents CLI spawn during tests)
        slack_mod.TRANSLATE_TITLES = False
    
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
        assert "Claude CLI未設定のため無効" in result  # Default summarization status
    
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
        assert "Claude CLI未設定のため無効" in result  # Default summarization status
    
    def test_format_verification_report_partially_verified(self):
        """Test formatting of partially verified report"""
        partially_verified_result = {
            "article_title": "Partially Verified AI News",
            "article_url": "https://example.com/partially-verified",
            "verification_status": "partially_verified",
            "total_related_count": 1,
            "related_articles": {"dev_to": [{"title": "Related"}], "medium": []},
            "checked_at": "2022-01-01 12:00:00 JST"
        }
        
        result = self.notifier.format_verification_report(partially_verified_result)
        
        assert "📊 AI News Verification Report" in result
        assert "🟡" in result  # Partially verified status emoji
        assert "1 related articles found" in result
        assert "dev.to(1), Medium(0)" in result
        assert "Claude CLI未設定のため無効" in result  # Default summarization status
    
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
        notifier = SlackNotifier(webhook_url="")  # Empty webhook URL
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
    
    def test_format_verification_report_with_summary(self):
        """Test formatting of verification report with summary"""
        verification_result_with_summary = {
            "article_title": "AI Article with Summary",
            "article_url": "https://example.com/ai-article",
            "verification_status": "verified",
            "total_related_count": 1,
            "related_articles": {"dev_to": [{"title": "Related"}], "medium": []},
            "checked_at": "2022-01-01 12:00:00 JST",
            "summary": "これはAI技術に関する重要な記事です。新しい機械学習手法について説明しています。",
            "summary_status": "success"
        }
        
        result = self.notifier.format_verification_report(verification_result_with_summary)
        
        assert "📝 **要約**:" in result
        assert "これはAI技術に関する重要な記事です。" in result
    
    def test_format_verification_report_summary_failed(self):
        """Test formatting of verification report with failed summary"""
        verification_result_failed = {
            "article_title": "AI Article",
            "article_url": "https://example.com/ai-article",
            "verification_status": "verified",
            "total_related_count": 1,
            "related_articles": {"dev_to": [], "medium": []},
            "checked_at": "2022-01-01 12:00:00 JST",
            "summary": None,
            "summary_status": "failed",
            "summary_error": "Claude CLI timeout"
        }
        
        result = self.notifier.format_verification_report(verification_result_failed)
        
        assert "📝 **要約**: 生成失敗 (Claude CLI timeout)" in result
