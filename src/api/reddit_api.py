"""Reddit API連携モジュール

Reddit APIを使用してAI関連のsubredditから投稿を取得し、
フィルタリングして構造化データとして返す機能を提供。
"""

import praw
import os
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class RedditPost:
    """Reddit投稿データクラス"""
    id: str
    title: str
    content: str
    url: str
    score: int
    num_comments: int
    created_utc: datetime
    author: str
    subreddit: str
    permalink: str
    flair_text: Optional[str] = None
    is_self: bool = False
    selftext: str = ""


class RedditAPI:
    """Reddit API クライアント"""
    
    def __init__(self):
        """
        Reddit APIクライアントを初期化
        
        環境変数から認証情報を取得:
        - REDDIT_CLIENT_ID: Reddit アプリケーションのクライアントID
        - REDDIT_CLIENT_SECRET: Reddit アプリケーションのクライアントシークレット
        - REDDIT_USER_AGENT: ユーザーエージェント文字列
        """
        self.client_id = os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = os.getenv('REDDIT_USER_AGENT', 'ai-news-feeder/1.0')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit API credentials not found in environment variables")
        
        # PRAW (Python Reddit API Wrapper) インスタンス初期化
        try:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            # 読み取り専用モードに設定
            self.reddit.read_only = True
            logger.info("Reddit API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API client: {e}")
            raise
    
    def get_subreddit_posts(self, subreddit_name: str, limit: int = 25, time_filter: str = "day") -> List[RedditPost]:
        """
        指定されたsubredditから投稿を取得
        
        Args:
            subreddit_name: subreddit名 (例: "MachineLearning")
            limit: 取得する投稿数の上限
            time_filter: 時間フィルター ("hour", "day", "week", "month", "year", "all")
        
        Returns:
            RedditPost オブジェクトのリスト
        
        Raises:
            Exception: API呼び出しエラー時
        """
        try:
            logger.info(f"Fetching posts from r/{subreddit_name} (limit: {limit}, time_filter: {time_filter})")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # 今日のホットな投稿を取得
            posts = []
            hot_posts = subreddit.hot(limit=limit)
            
            for submission in hot_posts:
                # 24時間以内の投稿のみを対象
                post_time = datetime.fromtimestamp(submission.created_utc)
                if datetime.now() - post_time > timedelta(hours=24):
                    continue
                
                # RedditPostオブジェクトに変換
                reddit_post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    content=submission.selftext if submission.is_self else "",
                    url=submission.url,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=post_time,
                    author=str(submission.author) if submission.author else "[deleted]",
                    subreddit=submission.subreddit.display_name,
                    permalink=f"https://reddit.com{submission.permalink}",
                    flair_text=submission.link_flair_text,
                    is_self=submission.is_self,
                    selftext=submission.selftext
                )
                posts.append(reddit_post)
                
                # レート制限を避けるため少し待機
                time.sleep(0.1)
            
            logger.info(f"Successfully fetched {len(posts)} posts from r/{subreddit_name}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            raise
    
    def filter_ai_related_posts(self, posts: List[RedditPost]) -> List[RedditPost]:
        """
        AI関連キーワードで投稿をフィルタリング
        
        Args:
            posts: RedditPost オブジェクトのリスト
        
        Returns:
            AI関連の投稿のみを含むリスト
        """
        # AI関連キーワード（設定から取得可能にする）
        ai_keywords = [
            "artificial intelligence", "machine learning", "deep learning",
            "neural network", "ChatGPT", "GPT", "Claude", "OpenAI", "AI",
            "LLM", "language model", "computer vision", "NLP", "natural language",
            "tensorflow", "pytorch", "hugging face", "transformer", "bert",
            "reinforcement learning", "supervised learning", "unsupervised learning",
            "data science", "ML", "DL", "AGI", "generative AI"
        ]
        
        filtered_posts = []
        
        for post in posts:
            # タイトル、本文、フレアでキーワード検索
            search_text = (
                post.title.lower() + " " + 
                post.content.lower() + " " + 
                (post.flair_text.lower() if post.flair_text else "")
            )
            
            # いずれかのキーワードが含まれているかチェック
            if any(keyword.lower() in search_text for keyword in ai_keywords):
                filtered_posts.append(post)
                logger.debug(f"AI-related post found: {post.title[:50]}...")
        
        logger.info(f"Filtered {len(filtered_posts)} AI-related posts from {len(posts)} total posts")
        return filtered_posts
    
    def filter_by_score(self, posts: List[RedditPost], min_score: int = 50) -> List[RedditPost]:
        """
        スコア（アップvotes）でフィルタリング
        
        Args:
            posts: RedditPost オブジェクトのリスト
            min_score: 最小スコア閾値
        
        Returns:
            指定スコア以上の投稿のみを含むリスト
        """
        filtered_posts = [post for post in posts if post.score >= min_score]
        logger.info(f"Filtered {len(filtered_posts)} posts with score >= {min_score}")
        return filtered_posts
    
    def get_ai_news_from_subreddits(self, subreddits: List[str], max_posts_per_sub: int = 10) -> List[RedditPost]:
        """
        複数のsubredditからAI関連ニュースを取得
        
        Args:
            subreddits: 監視対象のsubreddit名のリスト
            max_posts_per_sub: 各subredditから取得する投稿数の上限
        
        Returns:
            AI関連の投稿のリスト（スコア順でソート）
        """
        all_posts = []
        
        for subreddit_name in subreddits:
            try:
                # 各subredditから投稿を取得
                posts = self.get_subreddit_posts(subreddit_name, limit=max_posts_per_sub * 2)
                
                # AI関連でフィルタリング
                ai_posts = self.filter_ai_related_posts(posts)
                
                # スコアでフィルタリング
                score_filtered = self.filter_by_score(ai_posts, min_score=50)
                
                all_posts.extend(score_filtered)
                
                logger.info(f"Collected {len(score_filtered)} posts from r/{subreddit_name}")
                
                # Reddit API レート制限対応（1秒間隔）
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Failed to fetch from r/{subreddit_name}: {e}")
                continue
        
        # スコア順でソート（降順）
        all_posts.sort(key=lambda post: post.score, reverse=True)
        
        # 重複除去（同じURLの投稿を除去）
        unique_posts = []
        seen_urls = set()
        
        for post in all_posts:
            # URLの正規化
            parsed_url = urlparse(post.url)
            normalized_url = f"{parsed_url.netloc}{parsed_url.path}"
            
            if normalized_url not in seen_urls:
                unique_posts.append(post)
                seen_urls.add(normalized_url)
        
        logger.info(f"Final result: {len(unique_posts)} unique AI-related posts from {len(subreddits)} subreddits")
        return unique_posts[:max_posts_per_sub * len(subreddits)]  # 最大件数制限
    
    def convert_to_article_format(self, reddit_post: RedditPost) -> Dict:
        """
        RedditPostを既存のArticle形式に変換
        
        Args:
            reddit_post: RedditPost オブジェクト
        
        Returns:
            Article互換の辞書形式データ
        """
        return {
            "source": "reddit",
            "title": reddit_post.title,
            "url": reddit_post.url,
            "score": reddit_post.score,
            "time": reddit_post.created_utc.isoformat(),
            "source_specific": {
                "reddit_id": reddit_post.id,
                "subreddit": reddit_post.subreddit,
                "author": reddit_post.author,
                "num_comments": reddit_post.num_comments,
                "permalink": reddit_post.permalink,
                "flair_text": reddit_post.flair_text,
                "is_self": reddit_post.is_self,
                "selftext": reddit_post.selftext
            }
        }


def main():
    """テスト用のメイン関数"""
    # 環境変数の確認
    if not all([os.getenv('REDDIT_CLIENT_ID'), os.getenv('REDDIT_CLIENT_SECRET')]):
        print("Error: Reddit API credentials not found")
        print("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        return
    
    try:
        # Reddit APIクライアント初期化
        reddit_api = RedditAPI()
        
        # 監視対象のsubreddit
        subreddits = ["MachineLearning", "artificial", "singularity"]
        
        # AI関連投稿を取得
        posts = reddit_api.get_ai_news_from_subreddits(subreddits, max_posts_per_sub=5)
        
        print(f"\n=== Found {len(posts)} AI-related posts ===")
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. [{post.subreddit}] {post.title}")
            print(f"   Score: {post.score} | Comments: {post.num_comments}")
            print(f"   URL: {post.url}")
            print(f"   Time: {post.created_utc}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
