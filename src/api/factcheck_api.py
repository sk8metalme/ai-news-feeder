"""ファクトチェック用API（dev.to, Medium）"""
import requests
import feedparser
from typing import List, Dict
import logging
from urllib.parse import quote

from src.utils.config import Config

logger = logging.getLogger(__name__)


class FactCheckAPI:
    """dev.toとMediumでファクトチェックを行うAPI"""
    
    def __init__(self):
        self.dev_to_base = Config.DEV_TO_API_BASE
        self.medium_rss_base = Config.MEDIUM_RSS_BASE
        self.session = requests.Session()
        if Config.DEV_TO_API_KEY:
            self.session.headers['api-key'] = Config.DEV_TO_API_KEY
    
    def search_dev_to(self, query: str) -> List[Dict]:
        """dev.toで関連記事を検索"""
        try:
            # クエリから主要なキーワードを抽出
            keywords = self._extract_keywords(query)
            articles = []
            
            for keyword in keywords[:3]:  # 最初の3つのキーワードで検索
                url = f"{self.dev_to_base}/articles"
                params = {
                    'page': 1,
                    'per_page': 10,
                    'tag': keyword.lower().replace(' ', '')
                }
                
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    results = response.json()
                    for article in results:
                        # タイトルにキーワードが含まれているかチェック
                        if any(kw.lower() in article.get('title', '').lower() 
                               for kw in keywords):
                            articles.append({
                                'title': article.get('title'),
                                'url': article.get('url'),
                                'source': 'dev.to'
                            })
                
            return articles[:5]  # 最大5件返す
            
        except Exception as e:
            logger.error(f"dev.to検索エラー: {e}")
            return []
    
    def search_medium(self, query: str) -> List[Dict]:
        """MediumのRSSフィードで関連記事を検索"""
        try:
            keywords = self._extract_keywords(query)
            articles = []
            
            # AI関連のタグでRSSフィードを取得
            ai_tags = ['artificial-intelligence', 'machine-learning', 'ai', 'chatgpt', 'openai']
            
            for tag in ai_tags:
                feed_url = f"{self.medium_rss_base}{tag}"
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    continue
                
                for entry in feed.entries[:10]:  # 最新10件をチェック
                    title = entry.get('title', '').lower()
                    # キーワードマッチング
                    if any(keyword.lower() in title for keyword in keywords):
                        articles.append({
                            'title': entry.get('title'),
                            'url': entry.get('link'),
                            'source': 'Medium'
                        })
            
            return articles[:5]  # 最大5件返す
            
        except Exception as e:
            logger.error(f"Medium検索エラー: {e}")
            return []
    
    def verify_story(self, story_title: str) -> Dict:
        """ストーリーの信憑性を検証"""
        dev_to_results = self.search_dev_to(story_title)
        medium_results = self.search_medium(story_title)
        
        total_related = len(dev_to_results) + len(medium_results)
        
        return {
            'verified': total_related >= 1,  # 1件以上見つかれば信憑性ありと判定
            'related_count': total_related,
            'dev_to_count': len(dev_to_results),
            'medium_count': len(medium_results),
            'sources': {
                'dev_to': dev_to_results,
                'medium': medium_results
            }
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """テキストから主要なキーワードを抽出"""
        # 簡易的なキーワード抽出（本格的にはNLPライブラリを使用）
        keywords = []
        
        # AIキーワードで含まれているものを優先
        for keyword in Config.AI_KEYWORDS:
            if keyword.lower() in text.lower():
                keywords.append(keyword)
        
        # タイトルを単語に分割して、意味のありそうな単語を抽出
        words = text.split()
        for word in words:
            if len(word) > 4 and word[0].isupper():  # 5文字以上の大文字始まりの単語
                if word not in keywords:
                    keywords.append(word)
        
        return keywords[:5]  # 最大5個のキーワード