"""factcheck_api.pyのテスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import responses
import feedparser
from src.api.factcheck_api import FactCheckAPI


class TestFactCheckAPI:
    """FactCheckAPIクラスのテスト"""
    
    @pytest.fixture
    def api(self):
        """FactCheckAPIインスタンスを返す"""
        return FactCheckAPI()
    
    @responses.activate
    def test_search_dev_to_success(self, api):
        """dev.to検索が成功することを確認"""
        mock_response = [
            {
                'title': 'Understanding ChatGPT Architecture',
                'url': 'https://dev.to/user/chatgpt-architecture',
                'tags': ['ai', 'chatgpt'],
                'positive_reactions_count': 50
            },
            {
                'title': 'ChatGPT Best Practices',
                'url': 'https://dev.to/user/chatgpt-practices',
                'tags': ['chatgpt', 'tutorial'],
                'positive_reactions_count': 30
            }
        ]
        
        responses.add(
            responses.GET,
            f"{api.dev_to_base}/articles",
            json=mock_response,
            status=200
        )
        
        result = api.search_dev_to("ChatGPT New Features")
        
        assert len(result) > 0
        assert result[0]['source'] == 'dev.to'
        assert 'url' in result[0]
        assert 'title' in result[0]
    
    @responses.activate
    def test_search_dev_to_error(self, api):
        """dev.to検索エラー時の処理を確認"""
        responses.add(
            responses.GET,
            f"{api.dev_to_base}/articles",
            status=500
        )
        
        result = api.search_dev_to("Test Query")
        assert result == []
    
    @patch('feedparser.parse')
    def test_search_medium_success(self, mock_parse, api):
        """Medium検索が成功することを確認"""
        # フィードパーサーのモックレスポンス
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            MagicMock(
                title='Deep Dive into ChatGPT',
                link='https://medium.com/@user/chatgpt-deep-dive',
                summary='An article about ChatGPT'
            ),
            MagicMock(
                title='ChatGPT Applications',
                link='https://medium.com/@user/chatgpt-apps',
                summary='Practical uses of ChatGPT'
            )
        ]
        
        mock_parse.return_value = mock_feed
        
        result = api.search_medium("ChatGPT Technology")
        
        assert len(result) > 0
        assert result[0]['source'] == 'Medium'
        assert 'url' in result[0]
        assert 'title' in result[0]
    
    @patch('feedparser.parse')
    def test_search_medium_error(self, mock_parse, api):
        """Medium検索エラー時の処理を確認"""
        mock_parse.side_effect = Exception("Feed parsing error")
        
        result = api.search_medium("Test Query")
        assert result == []
    
    @patch('src.api.factcheck_api.FactCheckAPI.search_dev_to')
    @patch('src.api.factcheck_api.FactCheckAPI.search_medium')
    def test_verify_story_verified(self, mock_medium, mock_dev_to, api):
        """記事が検証済みと判定される場合のテスト"""
        mock_dev_to.return_value = [
            {'title': 'Related Article 1', 'url': 'https://dev.to/1', 'source': 'dev.to'},
            {'title': 'Related Article 2', 'url': 'https://dev.to/2', 'source': 'dev.to'}
        ]
        mock_medium.return_value = [
            {'title': 'Related Article 3', 'url': 'https://medium.com/1', 'source': 'Medium'}
        ]
        
        result = api.verify_story("ChatGPT New Features")
        
        assert result['verified'] is True
        assert result['related_count'] == 3
        assert result['dev_to_count'] == 2
        assert result['medium_count'] == 1
        assert len(result['sources']['dev_to']) == 2
        assert len(result['sources']['medium']) == 1
    
    @patch('src.api.factcheck_api.FactCheckAPI.search_dev_to')
    @patch('src.api.factcheck_api.FactCheckAPI.search_medium')
    def test_verify_story_not_verified(self, mock_medium, mock_dev_to, api):
        """記事が検証されない場合のテスト"""
        mock_dev_to.return_value = []
        mock_medium.return_value = []
        
        result = api.verify_story("Obscure Tech News")
        
        assert result['verified'] is False
        assert result['related_count'] == 0
        assert result['dev_to_count'] == 0
        assert result['medium_count'] == 0
    
    def test_extract_keywords(self, api):
        """キーワード抽出機能のテスト"""
        text = "ChatGPT and Claude are Leading AI Language Models"
        keywords = api._extract_keywords(text)
        
        assert "ChatGPT" in keywords
        assert "Claude" in keywords
        assert "AI" in keywords
        assert len(keywords) <= 5
    
    def test_extract_keywords_no_ai_terms(self, api):
        """AIキーワードが含まれない場合のキーワード抽出"""
        text = "Regular Technology News About Programming"
        keywords = api._extract_keywords(text)
        
        # 大文字始まりの長い単語が抽出される
        assert "Technology" in keywords
        assert "Programming" in keywords
    
    def test_api_key_header(self, monkeypatch):
        """APIキーが設定されている場合のヘッダー確認"""
        monkeypatch.setenv("DEV_TO_API_KEY", "test-api-key")
        
        # Configを再読み込み
        import importlib
        import src.utils.config
        importlib.reload(src.utils.config)
        
        # 新しいインスタンスを作成
        api = FactCheckAPI()
        assert api.session.headers.get('api-key') == 'test-api-key'
    
    def test_check_verification_criteria(self, api):
        """検証基準のチェックロジックをテスト"""
        # デフォルト設定（総数1以上）でテスト
        assert api._check_verification_criteria(1, 0, 1) is True
        assert api._check_verification_criteria(0, 0, 0) is False
        
        # 個別ソースの要件をテスト
        assert api._check_verification_criteria(2, 1, 1) is True
    
    def test_calculate_confidence_score(self, api):
        """信頼度スコア計算のテスト"""
        # 記事数0の場合
        assert api._calculate_confidence_score(0, 0, 0) == 0.0
        
        # 単一ソースからの記事
        score = api._calculate_confidence_score(5, 5, 0)
        assert 0.0 <= score <= 1.0
        
        # 複数ソースからの記事（多様性ボーナス）
        diverse_score = api._calculate_confidence_score(5, 3, 2)
        single_score = api._calculate_confidence_score(5, 5, 0)
        assert diverse_score > single_score  # 多様性がある方がスコアが高い
        
        # 最大スコア
        max_score = api._calculate_confidence_score(20, 12, 8)
        assert max_score == 1.0
    
    @patch('src.api.factcheck_api.FactCheckAPI.search_dev_to')
    @patch('src.api.factcheck_api.FactCheckAPI.search_medium')
    def test_verify_story_with_confidence(self, mock_medium, mock_dev_to, api):
        """信頼度スコアを含む検証結果のテスト"""
        mock_dev_to.return_value = [
            {'title': 'Article 1', 'url': 'https://dev.to/1', 'source': 'dev.to'},
            {'title': 'Article 2', 'url': 'https://dev.to/2', 'source': 'dev.to'},
            {'title': 'Article 3', 'url': 'https://dev.to/3', 'source': 'dev.to'}
        ]
        mock_medium.return_value = [
            {'title': 'Article 4', 'url': 'https://medium.com/1', 'source': 'Medium'},
            {'title': 'Article 5', 'url': 'https://medium.com/2', 'source': 'Medium'}
        ]
        
        result = api.verify_story("Test Article")
        
        assert result['verified'] is True
        assert result['related_count'] == 5
        assert 'confidence_score' in result
        assert 0.0 <= result['confidence_score'] <= 1.0
        assert result['confidence_score'] > 0.5  # 5記事あれば中程度以上の信頼度