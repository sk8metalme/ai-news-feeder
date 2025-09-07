"""Hacker News API クライアント"""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from src.utils.config import Config

logger = logging.getLogger(__name__)


class HackerNewsAPI:
    """Hacker News APIと通信するクライアント"""
    
    def __init__(self):
        self.base_url = Config.HACKERNEWS_API_BASE
        self.session = requests.Session()
    
    def get_top_stories(self, limit: int = 500) -> List[int]:
        """トップストーリーのIDリストを取得"""
        try:
            url = f"{self.base_url}/topstories.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:limit]
        except Exception as e:
            logger.error(f"トップストーリー取得エラー: {e}")
            return []
    
    def get_story(self, story_id: int) -> Optional[Dict]:
        """ストーリーの詳細を取得"""
        try:
            url = f"{self.base_url}/item/{story_id}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ストーリー{story_id}の取得エラー: {e}")
            return None
    
    def search_ai_stories(self, hours: int = 24) -> List[Dict]:
        """AI関連のストーリーを検索"""
        stories = []
        story_ids = self.get_top_stories()
        
        # 現在時刻と指定時間前の時刻を計算
        current_time = time.time()
        time_threshold = current_time - (hours * 3600)
        
        for story_id in story_ids:
            story = self.get_story(story_id)
            
            if not story:
                continue
            
            # 時間フィルタリング
            if story.get('time', 0) < time_threshold:
                continue
            
            # スコアフィルタリング
            if story.get('score', 0) < Config.MINIMUM_SCORE:
                continue
            
            # AIキーワードチェック
            title = story.get('title', '').lower()
            if any(keyword.lower() in title for keyword in Config.AI_KEYWORDS):
                stories.append(story)
                logger.info(f"AI関連記事を発見: {story.get('title')}")
            
            # API制限を考慮して少し待機
            time.sleep(0.1)
            
            # 必要な記事数に達したら終了
            if len(stories) >= Config.ARTICLES_PER_DAY * 2:  # 余裕を持って取得
                break
        
        # スコアで降順ソート
        stories.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return stories[:Config.ARTICLES_PER_DAY * 2]  # 検証で絞られるので多めに返す