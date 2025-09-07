"""Reddit API モジュールのテスト"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.api.reddit_api import RedditAPI, RedditPost


class TestRedditAPI:
    """RedditAPIクラスのテスト"""
    
    @pytest.fixture
    def mock_reddit_instance(self):
        """モックRedditインスタンス"""
        mock_reddit = Mock()
        mock_reddit.read_only = True
        return mock_reddit
    
    @pytest.fixture
    def sample_reddit_post(self):
        """サンプルReddit投稿データ"""
        return RedditPost(
            id="abc123",
            title="Revolutionary AI Model Achieves AGI",
            content="This is a groundbreaking discovery...",
            url="https://example.com/ai-news",
            score=150,
            num_comments=45,
            created_utc=datetime.now(),
            author="ai_researcher",
            subreddit="MachineLearning",
            permalink="/r/MachineLearning/comments/abc123/revolutionary_ai_model/",
            flair_text="Research",
            is_self=False,
            selftext=""
        )
    
    @pytest.fixture
    def mock_submission(self):
        """モックRedditサブミッション"""
        submission = Mock()
        submission.id = "abc123"
        submission.title = "AI Model Breakthrough"
        submission.selftext = "Detailed explanation..."
        submission.url = "https://example.com/ai-breakthrough"
        submission.score = 200
        submission.num_comments = 50
        submission.created_utc = datetime.now().timestamp()
        submission.author = Mock()
        submission.author.__str__ = Mock(return_value="researcher")
        submission.subreddit.display_name = "MachineLearning"
        submission.permalink = "/r/MachineLearning/comments/abc123/"
        submission.link_flair_text = "Research"
        submission.is_self = False
        return submission
    
    def test_init_success(self, mock_reddit_instance):
        """初期化成功テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_client_id',
            'REDDIT_CLIENT_SECRET': 'test_client_secret',
            'REDDIT_USER_AGENT': 'test_agent'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                api = RedditAPI()
                assert api.client_id == 'test_client_id'
                assert api.client_secret == 'test_client_secret'
                assert api.user_agent == 'test_agent'
    
    def test_init_missing_credentials(self):
        """認証情報不足時のエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Reddit API credentials not found"):
                RedditAPI()
    
    def test_init_with_praw_error(self):
        """PRAW初期化エラーテスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_client_id',
            'REDDIT_CLIENT_SECRET': 'test_client_secret'
        }):
            with patch('praw.Reddit', side_effect=Exception("API Error")):
                with pytest.raises(Exception, match="API Error"):
                    RedditAPI()
    
    @patch('time.sleep')
    def test_get_subreddit_posts_success(self, mock_sleep, mock_reddit_instance, mock_submission):
        """subreddit投稿取得成功テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                # モックsubredditとhot()の設定
                mock_subreddit = Mock()
                mock_subreddit.hot.return_value = [mock_submission]
                mock_reddit_instance.subreddit.return_value = mock_subreddit
                
                api = RedditAPI()
                posts = api.get_subreddit_posts("MachineLearning", limit=10)
                
                assert len(posts) == 1
                assert posts[0].title == "AI Model Breakthrough"
                assert posts[0].score == 200
                assert posts[0].subreddit == "MachineLearning"
    
    @patch('time.sleep')
    def test_get_subreddit_posts_old_posts_filtered(self, mock_sleep, mock_reddit_instance):
        """古い投稿のフィルタリングテスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                # 2日前の投稿（フィルタされるべき）
                old_submission = Mock()
                old_submission.created_utc = (datetime.now() - timedelta(days=2)).timestamp()
                old_submission.title = "Old AI News"
                
                mock_subreddit = Mock()
                mock_subreddit.hot.return_value = [old_submission]
                mock_reddit_instance.subreddit.return_value = mock_subreddit
                
                api = RedditAPI()
                posts = api.get_subreddit_posts("MachineLearning")
                
                assert len(posts) == 0  # 古い投稿は除外される
    
    def test_filter_ai_related_posts(self, sample_reddit_post):
        """AI関連投稿フィルタリングテスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit'):
                api = RedditAPI()
                
                # AI関連投稿
                ai_post = RedditPost(
                    id="1", title="Machine Learning Breakthrough", content="AI model...",
                    url="https://example.com", score=100, num_comments=10,
                    created_utc=datetime.now(), author="user", subreddit="ML",
                    permalink="/r/ML/1"
                )
                
                # 非AI関連投稿
                non_ai_post = RedditPost(
                    id="2", title="Cooking Recipe", content="How to cook...",
                    url="https://cooking.com", score=50, num_comments=5,
                    created_utc=datetime.now(), author="chef", subreddit="cooking",
                    permalink="/r/cooking/2"
                )
                
                posts = [ai_post, non_ai_post]
                filtered = api.filter_ai_related_posts(posts)
                
                assert len(filtered) == 1
                assert filtered[0].title == "Machine Learning Breakthrough"
    
    def test_filter_by_score(self, sample_reddit_post):
        """スコアフィルタリングテスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit'):
                api = RedditAPI()
                
                high_score_post = RedditPost(
                    id="1", title="High Score Post", content="Content",
                    url="https://example.com", score=100, num_comments=10,
                    created_utc=datetime.now(), author="user", subreddit="ML",
                    permalink="/r/ML/1"
                )
                
                low_score_post = RedditPost(
                    id="2", title="Low Score Post", content="Content",
                    url="https://example2.com", score=10, num_comments=2,
                    created_utc=datetime.now(), author="user2", subreddit="ML",
                    permalink="/r/ML/2"
                )
                
                posts = [high_score_post, low_score_post]
                filtered = api.filter_by_score(posts, min_score=50)
                
                assert len(filtered) == 1
                assert filtered[0].score == 100
    
    @patch('time.sleep')
    def test_get_ai_news_from_subreddits(self, mock_sleep, mock_reddit_instance):
        """複数subredditからのAI関連ニュース取得テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                api = RedditAPI()
                
                # get_subreddit_postsをモック
                with patch.object(api, 'get_subreddit_posts') as mock_get_posts:
                    with patch.object(api, 'filter_ai_related_posts') as mock_filter_ai:
                        with patch.object(api, 'filter_by_score') as mock_filter_score:
                            
                            # モックの戻り値設定
                            mock_get_posts.return_value = [sample_reddit_post]
                            mock_filter_ai.return_value = [sample_reddit_post]
                            mock_filter_score.return_value = [sample_reddit_post]
                            
                            subreddits = ["MachineLearning", "artificial"]
                            posts = api.get_ai_news_from_subreddits(subreddits, max_posts_per_sub=5)
                            
                            assert len(posts) == 2  # 2つのsubredditから1つずつ
                            assert mock_get_posts.call_count == 2
    
    def test_convert_to_article_format(self, sample_reddit_post):
        """Article形式変換テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit'):
                api = RedditAPI()
                article = api.convert_to_article_format(sample_reddit_post)
                
                assert article["source"] == "reddit"
                assert article["title"] == sample_reddit_post.title
                assert article["url"] == sample_reddit_post.url
                assert article["score"] == sample_reddit_post.score
                assert article["source_specific"]["subreddit"] == "MachineLearning"
                assert article["source_specific"]["reddit_id"] == "abc123"
    
    def test_get_subreddit_posts_api_error(self, mock_reddit_instance):
        """API エラー時のテスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                mock_reddit_instance.subreddit.side_effect = Exception("API Error")
                
                api = RedditAPI()
                
                with pytest.raises(Exception, match="API Error"):
                    api.get_subreddit_posts("MachineLearning")
    
    @patch('time.sleep')
    def test_get_ai_news_subreddit_error_handling(self, mock_sleep, mock_reddit_instance):
        """subredditエラー時の継続処理テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                api = RedditAPI()
                
                with patch.object(api, 'get_subreddit_posts') as mock_get_posts:
                    # 最初のsubredditでエラー、2番目は成功
                    mock_get_posts.side_effect = [Exception("Error"), []]
                    
                    subreddits = ["BadSubreddit", "GoodSubreddit"]
                    posts = api.get_ai_news_from_subreddits(subreddits)
                    
                    # エラーが発生しても処理が継続される
                    assert isinstance(posts, list)
                    assert mock_get_posts.call_count == 2
    
    def test_deduplication_by_url(self, mock_reddit_instance):
        """URL重複除去テスト"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_id',
            'REDDIT_CLIENT_SECRET': 'test_secret'
        }):
            with patch('praw.Reddit', return_value=mock_reddit_instance):
                api = RedditAPI()
                
                # 同じURLの投稿を2つ作成
                post1 = RedditPost(
                    id="1", title="Post 1", content="", url="https://example.com/article",
                    score=100, num_comments=10, created_utc=datetime.now(),
                    author="user1", subreddit="ML", permalink="/r/ML/1"
                )
                
                post2 = RedditPost(
                    id="2", title="Post 2", content="", url="https://example.com/article",
                    score=80, num_comments=5, created_utc=datetime.now(),
                    author="user2", subreddit="AI", permalink="/r/AI/2"
                )
                
                with patch.object(api, 'get_subreddit_posts', return_value=[post1, post2]):
                    with patch.object(api, 'filter_ai_related_posts', side_effect=lambda x: x):
                        with patch.object(api, 'filter_by_score', side_effect=lambda x, **kwargs: x):
                            
                            posts = api.get_ai_news_from_subreddits(["test"])
                            
                            # 重複除去により1件のみ残る（スコアが高い方）
                            assert len(posts) == 1
                            assert posts[0].score == 100
