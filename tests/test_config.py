"""config.pyのテスト"""
import pytest
from src.utils.config import Config


class TestConfig:
    """Configクラスのテスト"""
    
    def test_config_loads_from_env(self):
        """環境変数から設定が正しく読み込まれることを確認"""
        assert Config.SLACK_WEBHOOK_URL == "https://hooks.slack.com/services/TEST/WEBHOOK/URL"
        assert Config.ARTICLES_PER_DAY == 5
        assert Config.MINIMUM_SCORE == 50
        assert Config.RUN_HOUR == 9
    
    def test_ai_keywords_exist(self):
        """AIキーワードが定義されていることを確認"""
        assert len(Config.AI_KEYWORDS) > 0
        assert "ChatGPT" in Config.AI_KEYWORDS
        assert "Claude" in Config.AI_KEYWORDS
        assert "AI" in Config.AI_KEYWORDS
        assert "LLM" in Config.AI_KEYWORDS
        assert "OpenAI" in Config.AI_KEYWORDS
    
    def test_api_urls_defined(self):
        """API URLが定義されていることを確認"""
        assert Config.HACKERNEWS_API_BASE == "https://hacker-news.firebaseio.com/v0"
        assert Config.DEV_TO_API_BASE == "https://dev.to/api"
        assert Config.MEDIUM_RSS_BASE == "https://medium.com/feed/tag/"
    
    def test_validate_success(self):
        """正常な設定での検証が成功することを確認"""
        assert Config.validate() is True
    
    def test_validate_missing_webhook(self, monkeypatch):
        """Webhook URLが未設定の場合にエラーが発生することを確認"""
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "")
        # Configクラスを再読み込み
        import importlib
        import src.utils.config
        importlib.reload(src.utils.config)
        from src.utils.config import Config as ReloadedConfig
        
        with pytest.raises(ValueError, match="SLACK_WEBHOOK_URLが設定されていません"):
            ReloadedConfig.validate()
    
    def test_validate_invalid_articles_per_day(self, monkeypatch):
        """ARTICLES_PER_DAYが範囲外の場合にエラーが発生することを確認"""
        monkeypatch.setenv("ARTICLES_PER_DAY", "25")
        # Configクラスを再読み込み
        import importlib
        import src.utils.config
        importlib.reload(src.utils.config)
        from src.utils.config import Config as ReloadedConfig
        
        with pytest.raises(ValueError, match="ARTICLES_PER_DAYは1-20の範囲で設定してください"):
            ReloadedConfig.validate()
    
    def test_default_values(self, monkeypatch):
        """環境変数が未設定の場合のデフォルト値を確認"""
        # 特定の環境変数を削除
        monkeypatch.delenv("ARTICLES_PER_DAY", raising=False)
        monkeypatch.delenv("MINIMUM_SCORE", raising=False)
        monkeypatch.delenv("RUN_HOUR", raising=False)
        
        # Configクラスを再読み込み
        import importlib
        import src.utils.config
        importlib.reload(src.utils.config)
        from src.utils.config import Config as ReloadedConfig
        
        assert ReloadedConfig.ARTICLES_PER_DAY == 5
        assert ReloadedConfig.MINIMUM_SCORE == 50
        assert ReloadedConfig.RUN_HOUR == 9