"""hackernews_api.pyのテスト"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import responses
from src.api.hackernews_api import HackerNewsAPI


class TestHackerNewsAPI:
    """HackerNewsAPIクラスのテスト"""
    
    @pytest.fixture
    def api(self):
        """HackerNewsAPIインスタンスを返す"""
        return HackerNewsAPI()
    
    @responses.activate
    def test_get_top_stories_success(self, api):
        """トップストーリーの取得が成功することを確認"""
        # モックレスポンスを設定
        story_ids = [1001, 1002, 1003, 1004, 1005]
        responses.add(
            responses.GET,
            f"{api.base_url}/topstories.json",
            json=story_ids,
            status=200
        )
        
        result = api.get_top_stories(limit=3)
        assert result == [1001, 1002, 1003]
    
    @responses.activate
    def test_get_top_stories_error(self, api):
        """トップストーリー取得時のエラーハンドリングを確認"""
        responses.add(
            responses.GET,
            f"{api.base_url}/topstories.json",
            status=500
        )
        
        result = api.get_top_stories()
        assert result == []
    
    @responses.activate
    def test_get_story_success(self, api):
        """ストーリー詳細の取得が成功することを確認"""
        story_data = {
            'id': 1001,
            'title': 'Test Story',
            'url': 'https://example.com',
            'score': 100,
            'time': 1693900000,
            'type': 'story'
        }
        responses.add(
            responses.GET,
            f"{api.base_url}/item/1001.json",
            json=story_data,
            status=200
        )
        
        result = api.get_story(1001)
        assert result == story_data
    
    @responses.activate
    def test_get_story_error(self, api):
        """ストーリー詳細取得時のエラーハンドリングを確認"""
        responses.add(
            responses.GET,
            f"{api.base_url}/item/1001.json",
            status=404
        )
        
        result = api.get_story(1001)
        assert result is None
    
    @patch('src.api.hackernews_api.HackerNewsAPI.get_top_stories')
    @patch('src.api.hackernews_api.HackerNewsAPI.get_story')
    def test_search_ai_stories(self, mock_get_story, mock_get_top_stories, api):
        """AI関連ストーリーの検索が正しく動作することを確認"""
        # モックの設定
        mock_get_top_stories.return_value = [1001, 1002, 1003, 1004, 1005]
        
        current_time = time.time()
        stories = [
            {
                'id': 1001,
                'title': 'ChatGPT New Features Released',
                'url': 'https://example.com/1',
                'score': 200,
                'time': current_time - 3600,  # 1時間前
                'type': 'story'
            },
            {
                'id': 1002,
                'title': 'Regular Tech News',
                'url': 'https://example.com/2',
                'score': 150,
                'time': current_time - 7200,  # 2時間前
                'type': 'story'
            },
            {
                'id': 1003,
                'title': 'Claude API Updates',
                'url': 'https://example.com/3',
                'score': 180,
                'time': current_time - 10800,  # 3時間前
                'type': 'story'
            },
            {
                'id': 1004,
                'title': 'Old AI News',
                'url': 'https://example.com/4',
                'score': 100,
                'time': current_time - 100000,  # 古すぎる
                'type': 'story'
            },
            {
                'id': 1005,
                'title': 'Low Score AI Article',
                'url': 'https://example.com/5',
                'score': 30,  # スコアが低い
                'time': current_time - 3600,
                'type': 'story'
            }
        ]
        
        mock_get_story.side_effect = stories
        
        result = api.search_ai_stories(hours=24)
        
        # AI関連記事のみが返されることを確認
        assert len(result) == 2
        assert result[0]['title'] == 'ChatGPT New Features Released'
        assert result[1]['title'] == 'Claude API Updates'
        
        # スコアで降順ソートされていることを確認
        assert result[0]['score'] >= result[1]['score']
    
    @patch('src.api.hackernews_api.HackerNewsAPI.get_top_stories')
    @patch('src.api.hackernews_api.HackerNewsAPI.get_story')
    def test_search_ai_stories_empty(self, mock_get_story, mock_get_top_stories, api):
        """AI関連記事が見つからない場合の動作を確認"""
        mock_get_top_stories.return_value = [1001, 1002]
        
        current_time = time.time()
        stories = [
            {
                'id': 1001,
                'title': 'Regular Tech News',
                'url': 'https://example.com/1',
                'score': 200,
                'time': current_time - 3600,
                'type': 'story'
            },
            {
                'id': 1002,
                'title': 'Another Regular News',
                'url': 'https://example.com/2',
                'score': 150,
                'time': current_time - 7200,
                'type': 'story'
            }
        ]
        
        mock_get_story.side_effect = stories
        
        result = api.search_ai_stories(hours=24)
        assert result == []
    
    def test_session_persistence(self, api):
        """HTTPセッションが再利用されることを確認"""
        session1 = api.session
        session2 = api.session
        assert session1 is session2