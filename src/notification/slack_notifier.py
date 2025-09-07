"""
Slack notification module for posting AI news reports
"""
import requests
import json
from typing import Dict, List
from ..utils.logger import get_logger
from config.settings import SLACK_WEBHOOK_URL, SLACK_CHANNEL

logger = get_logger(__name__)


class SlackNotifier:
    """Class for sending notifications to Slack"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url if webhook_url is not None else SLACK_WEBHOOK_URL
        
    def format_verification_report(self, verification_result: Dict) -> str:
        """Format verification result into Slack message"""
        article_title = verification_result.get('article_title', 'Unknown')
        article_url = verification_result.get('article_url', '')
        status = verification_result.get('verification_status', 'unknown')
        total_count = verification_result.get('total_related_count', 0)
        checked_at = verification_result.get('checked_at', '')
        
        dev_to_count = len(verification_result.get('related_articles', {}).get('dev_to', []))
        medium_count = len(verification_result.get('related_articles', {}).get('medium', []))
        
        # Create status emoji
        if status == "verified":
            status_emoji = "✅"
        elif status == "partially_verified":
            status_emoji = "🟡"
        else:
            status_emoji = "❌"
        
        message = f"""📊 AI News Verification Report
{status_emoji} **Topic**: {article_title}
🔗 **Source**: Hacker News
📈 **Verified**: {total_count} related articles found
📚 **Links**: dev.to({dev_to_count}), Medium({medium_count})
🌐 **URL**: {article_url}
⏰ **Checked**: {checked_at}"""
        
        # Add summary if available
        summary = verification_result.get('summary')
        summary_status = verification_result.get('summary_status', 'disabled')
        
        if summary_status == 'success' and summary:
            message += f"""

📝 **要約**:
{summary}"""
        elif summary_status == 'failed':
            summary_error = verification_result.get('summary_error', '不明なエラー')
            message += f"""

📝 **要約**: 生成失敗 ({summary_error})"""
        elif summary_status == 'disabled':
            message += f"""

📝 **要約**: Claude CLI未設定のため無効"""
        
        return message
    
    def send_notification(self, message: str, channel: str = None) -> bool:
        """Send a message to Slack"""
        if not self.webhook_url or self.webhook_url.strip() == "":
            logger.error("Slack webhook URL not configured")
            return False
        
        payload = {
            "text": message,
            "channel": channel or SLACK_CHANNEL,
            "username": "AI News Bot",
            "icon_emoji": ":robot_face:"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Successfully sent notification to Slack")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def send_verification_report(self, verification_result: Dict, channel: str = None) -> bool:
        """Send a formatted verification report to Slack"""
        message = self.format_verification_report(verification_result)
        return self.send_notification(message, channel)
    
    def send_daily_summary(self, verification_results: List[Dict], channel: str = None) -> bool:
        """Send a daily summary of all verified articles"""
        if not verification_results:
            message = "📊 Daily AI News Summary\n\n❌ No verified AI articles found today."
        else:
            verified_count = sum(1 for result in verification_results 
                               if result.get('verification_status') == 'verified')
            partially_verified_count = sum(1 for result in verification_results 
                                         if result.get('verification_status') == 'partially_verified')
            total_count = len(verification_results)
            unverified_count = total_count - verified_count - partially_verified_count
            
            message = f"""📊 Daily AI News Summary
📈 **Total Articles Processed**: {total_count}
✅ **Verified Articles**: {verified_count}
🟡 **Partially Verified Articles**: {partially_verified_count}
❌ **Unverified Articles**: {unverified_count}

**Verified & Partially Verified Articles:**"""
            
            for result in verification_results:
                status = result.get('verification_status')
                if status in ['verified', 'partially_verified']:
                    title = result.get('article_title', 'Unknown')
                    url = result.get('article_url', '')
                    count = result.get('total_related_count', 0)
                    emoji = "✅" if status == "verified" else "🟡"
                    message += f"\n{emoji} {title} ({count} sources) - {url}"
        
        return self.send_notification(message, channel)
