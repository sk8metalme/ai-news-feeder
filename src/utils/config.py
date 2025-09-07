"""設定管理モジュール"""
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

class Config:
    """アプリケーション設定"""
    
    # Slack設定
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # API設定
    DEV_TO_API_KEY = os.getenv("DEV_TO_API_KEY", "")
    
    # 実行設定
    ARTICLES_PER_DAY = int(os.getenv("ARTICLES_PER_DAY", "5"))
    MINIMUM_SCORE = int(os.getenv("MINIMUM_SCORE", "50"))
    RUN_HOUR = int(os.getenv("RUN_HOUR", "9"))
    
    # ファクトチェック設定
    FACTCHECK_MIN_SOURCES = int(os.getenv("FACTCHECK_MIN_SOURCES", "1"))  # 最低限必要な関連記事数
    FACTCHECK_MIN_DEV_TO = int(os.getenv("FACTCHECK_MIN_DEV_TO", "0"))  # dev.toの最低記事数
    FACTCHECK_MIN_MEDIUM = int(os.getenv("FACTCHECK_MIN_MEDIUM", "0"))  # Mediumの最低記事数
    FACTCHECK_CONFIDENCE_THRESHOLD = float(os.getenv("FACTCHECK_CONFIDENCE_THRESHOLD", "0.5"))  # 信頼度閾値
    
    # AIキーワード
    AI_KEYWORDS = [
        "ChatGPT",
        "Claude",
        "AI",
        "LLM",
        "OpenAI",
        "Google AI",
        "GPT-4",
        "artificial intelligence",
        "machine learning",
        "deep learning"
    ]
    
    # API URL
    HACKERNEWS_API_BASE = "https://hacker-news.firebaseio.com/v0"
    DEV_TO_API_BASE = "https://dev.to/api"
    MEDIUM_RSS_BASE = "https://medium.com/feed/tag/"
    
    @classmethod
    def validate(cls):
        """設定の検証"""
        if not cls.SLACK_WEBHOOK_URL:
            raise ValueError("SLACK_WEBHOOK_URLが設定されていません")
        
        if cls.ARTICLES_PER_DAY < 1 or cls.ARTICLES_PER_DAY > 20:
            raise ValueError("ARTICLES_PER_DAYは1-20の範囲で設定してください")
        
        return True