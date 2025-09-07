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
        dev_to_count = len(dev_to_results)
        medium_count = len(medium_results)
        
        # 複数の検証基準を適用
        verified = self._check_verification_criteria(
            total_related, dev_to_count, medium_count
        )
        
        # 信頼度スコアを計算
        confidence_score = self._calculate_confidence_score(
            total_related, dev_to_count, medium_count
        )
        
        return {
            'verified': verified,
            'related_count': total_related,
            'dev_to_count': dev_to_count,
            'medium_count': medium_count,
            'confidence_score': confidence_score,
            'sources': {
                'dev_to': dev_to_results,
                'medium': medium_results
            }
        }
    
    def _check_verification_criteria(self, total: int, dev_to: int, medium: int) -> bool:
        """検証基準をチェック"""
        # 総数が最低限必要な数を満たしているか
        if total < Config.FACTCHECK_MIN_SOURCES:
            return False
        
        # 個別のソースの最低要件をチェック
        if dev_to < Config.FACTCHECK_MIN_DEV_TO:
            return False
        
        if medium < Config.FACTCHECK_MIN_MEDIUM:
            return False
        
        return True
    
    def _calculate_confidence_score(self, total: int, dev_to: int, medium: int) -> float:
        """信頼度スコアを計算（0.0-1.0）"""
        if total == 0:
            return 0.0
        
        # 基本スコア（記事数に基づく）
        base_score = min(total / 10.0, 1.0)  # 10記事で最大スコア
        
        # ソースの多様性ボーナス
        diversity_bonus = 0.0
        if dev_to > 0 and medium > 0:
            diversity_bonus = 0.2  # 両方のソースから記事がある場合
        
        # 記事数に応じた重み付け
        dev_to_weight = 0.6  # dev.toの重み
        medium_weight = 0.4  # Mediumの重み
        
        weighted_score = (
            (dev_to * dev_to_weight + medium * medium_weight) / 
            max(total * (dev_to_weight + medium_weight) / 2, 1)
        )
        
        # 最終スコア
        final_score = (base_score * 0.7 + weighted_score * 0.3 + diversity_bonus)
        
        return min(final_score, 1.0)
    
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