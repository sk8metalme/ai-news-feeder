"""Slack通知モジュール"""
import requests
import json
from typing import Dict, List
from datetime import datetime
import logging

from src.utils.config import Config

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Slackへの通知を管理するクラス"""
    
    def __init__(self):
        self.webhook_url = Config.SLACK_WEBHOOK_URL
    
    def send_verification_report(self, articles: List[Dict]) -> bool:
        """検証レポートをSlackに送信"""
        try:
            # レポートのヘッダー
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 AI News Verification Report"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:* {datetime.now().strftime('%Y/%m/%d %H:%M')} JST"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ]
            
            # 各記事の情報を追加
            for article in articles:
                blocks.extend(self._create_article_blocks(article))
            
            # フッター
            blocks.extend([
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Total verified articles: {len(articles)}_"
                        }
                    ]
                }
            ])
            
            # Slackに送信
            payload = {
                "blocks": blocks,
                "text": f"AI News Report - {len(articles)} verified articles"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slackに{len(articles)}件の記事を送信しました")
                return True
            else:
                logger.error(f"Slack送信エラー: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Slack通知エラー: {e}")
            return False
    
    def _create_article_blocks(self, article: Dict) -> List[Dict]:
        """記事情報のブロックを作成"""
        verification = article.get('verification', {})
        
        # 記事タイトルとスコア
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Topic:* {article['title']}\n*Source:* Hacker News (Score: {article['score']})"
                }
            }
        ]
        
        # 検証結果
        verified_text = "✅ Verified" if verification.get('verified') else "❌ Not Verified"
        related_count = verification.get('related_count', 0)
        dev_to_count = verification.get('dev_to_count', 0)
        medium_count = verification.get('medium_count', 0)
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{verified_text}:* {related_count} related articles found\n" +
                        f"*Links:* dev.to({dev_to_count}), Medium({medium_count})"
            }
        })
        
        # URL
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*URL:* <{article['url']}|View Article>"
            }
        })
        
        # 検証時刻
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Checked: {datetime.now().strftime('%Y/%m/%d %H:%M')} JST"
                }
            ]
        })
        
        # 区切り線
        blocks.append({"type": "divider"})
        
        return blocks
    
    def send_error_notification(self, error_message: str) -> bool:
        """エラー通知をSlackに送信"""
        try:
            payload = {
                "text": f"⚠️ AI News Feeder Error",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": "Error Details",
                                "value": error_message,
                                "short": False
                            },
                            {
                                "title": "Time",
                                "value": datetime.now().strftime('%Y/%m/%d %H:%M JST'),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"エラー通知送信失敗: {e}")
            return False