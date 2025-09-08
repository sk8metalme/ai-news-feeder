"""GitHub Trending API モジュールのテスト"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.api.github_trending import GitHubTrendingAPI, GitHubRepository


class TestGitHubTrendingAPI:
    """GitHubTrendingAPIクラスのテスト"""
    
    @pytest.fixture
    def mock_github_instance(self):
        """モックGitHubインスタンス"""
        mock_github = Mock()
        mock_user = Mock()
        mock_user.login = "test_user"
        mock_github.get_user.return_value = mock_user
        return mock_github
    
    @pytest.fixture
    def sample_github_repo(self):
        """サンプルGitHubリポジトリデータ"""
        return GitHubRepository(
            id=12345,
            name="awesome-ai-project",
            full_name="user/awesome-ai-project",
            description="Revolutionary AI framework for machine learning",
            url="https://github.com/user/awesome-ai-project",
            stars_count=1500,
            today_stars=25,
            language="Python",
            topics=["machine-learning", "artificial-intelligence", "deep-learning"],
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(hours=2),
            pushed_at=datetime.now() - timedelta(hours=1),
            owner="user",
            readme_content="# Awesome AI Project\n\nThis is a revolutionary AI framework...",
            size=2048,
            forks_count=200,
            watchers_count=300,
            open_issues_count=15
        )
    
    @pytest.fixture
    def mock_repository(self):
        """モックGitHubリポジトリ（PyGitHub形式）"""
        repo = Mock()
        repo.id = 12345
        repo.name = "ai-framework"
        repo.full_name = "user/ai-framework"
        repo.description = "AI framework for machine learning"
        repo.html_url = "https://github.com/user/ai-framework"
        repo.stargazers_count = 500
        repo.language = "Python"
        repo.created_at = datetime.now() - timedelta(days=10)
        repo.updated_at = datetime.now() - timedelta(hours=1)
        repo.pushed_at = datetime.now() - timedelta(minutes=30)
        repo.owner.login = "user"
        repo.size = 1024
        repo.forks_count = 50
        repo.watchers_count = 75
        repo.open_issues_count = 5
        
        # get_topics() モック
        repo.get_topics.return_value = ["machine-learning", "python"]
        
        # get_readme() モック
        mock_readme = Mock()
        mock_readme.decoded_content = b"# AI Framework\n\nMachine learning toolkit"
        repo.get_readme.return_value = mock_readme
        
        return repo
    
    def test_init_success(self, mock_github_instance):
        """初期化成功テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                assert api.access_token == 'test_token'
    
    def test_init_missing_token(self):
        """アクセストークン不足時のエラーテスト"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GitHub access token not found"):
                GitHubTrendingAPI()
    
    def test_init_with_github_error(self):
        """GitHub初期化エラーテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', side_effect=Exception("GitHub API Error")):
                with pytest.raises(Exception, match="GitHub API Error"):
                    GitHubTrendingAPI()
    
    @patch('time.sleep')
    def test_get_trending_repositories_success(self, mock_sleep, mock_github_instance, mock_repository):
        """トレンディングリポジトリ取得成功テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                # search_repositories モック設定
                mock_github_instance.search_repositories.return_value = [mock_repository]
                
                api = GitHubTrendingAPI()
                repos = api.get_trending_repositories(language="python", since="daily")
                
                assert len(repos) == 1
                assert repos[0].name == "ai-framework"
                assert repos[0].language == "Python"
                assert repos[0].stars_count == 500
    
    def test_convert_to_github_repository(self, mock_github_instance, mock_repository):
        """PyGitHub Repository変換テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                github_repo = api._convert_to_github_repository(mock_repository)
                
                assert github_repo.id == 12345
                assert github_repo.name == "ai-framework"
                assert github_repo.full_name == "user/ai-framework"
                assert github_repo.stars_count == 500
                assert github_repo.language == "Python"
                assert github_repo.topics == ["machine-learning", "python"]
                assert "AI Framework" in github_repo.readme_content
    
    def test_convert_repository_with_errors(self, mock_github_instance, mock_repository):
        """リポジトリ変換時のエラーハンドリングテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                # get_topics()でエラーが発生する場合
                mock_repository.get_topics.side_effect = Exception("Topics API Error")
                # get_readme()でエラーが発生する場合  
                mock_repository.get_readme.side_effect = Exception("README API Error")
                
                api = GitHubTrendingAPI()
                github_repo = api._convert_to_github_repository(mock_repository)
                
                # エラーがあっても基本情報は取得される
                assert github_repo.name == "ai-framework"
                assert github_repo.topics == []  # エラー時は空リスト
                assert github_repo.readme_content is None  # エラー時はNone
    
    def test_filter_ai_repositories(self, mock_github_instance, sample_github_repo):
        """AI関連リポジトリフィルタリングテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                
                # AI関連リポジトリ
                ai_repo = GitHubRepository(
                    id=1, name="ml-toolkit", full_name="user/ml-toolkit",
                    description="Machine learning toolkit for AI researchers",
                    url="https://github.com/user/ml-toolkit", stars_count=100,
                    today_stars=5, language="Python", 
                    topics=["machine-learning", "ai"],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                # 非AI関連リポジトリ
                non_ai_repo = GitHubRepository(
                    id=2, name="web-app", full_name="user/web-app",
                    description="Simple web application for e-commerce",
                    url="https://github.com/user/web-app", stars_count=50,
                    today_stars=2, language="JavaScript",
                    topics=["web", "ecommerce"],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                repos = [ai_repo, non_ai_repo]
                filtered = api.filter_ai_repositories(repos)
                
                assert len(filtered) == 1
                assert filtered[0].name == "ml-toolkit"
    
    def test_filter_by_stars(self, mock_github_instance, sample_github_repo):
        """Star数フィルタリングテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                
                high_star_repo = GitHubRepository(
                    id=1, name="popular-repo", full_name="user/popular-repo",
                    description="Popular repository", url="https://github.com/user/popular-repo",
                    stars_count=100, today_stars=5, language="Python", topics=[],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                low_star_repo = GitHubRepository(
                    id=2, name="small-repo", full_name="user/small-repo",
                    description="Small repository", url="https://github.com/user/small-repo",
                    stars_count=5, today_stars=1, language="Python", topics=[],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                repos = [high_star_repo, low_star_repo]
                filtered = api.filter_by_stars(repos, min_stars=50)
                
                assert len(filtered) == 1
                assert filtered[0].stars_count == 100
    
    @patch('time.sleep')
    def test_get_ai_trending_repositories(self, mock_sleep, mock_github_instance, sample_github_repo):
        """AI関連トレンディングリポジトリ取得テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                
                # メソッドをモック
                with patch.object(api, 'get_trending_repositories') as mock_get_trending:
                    with patch.object(api, 'filter_ai_repositories') as mock_filter_ai:
                        with patch.object(api, 'filter_by_stars') as mock_filter_stars:
                            
                            # モックの戻り値設定
                            mock_get_trending.return_value = [sample_github_repo]
                            mock_filter_ai.return_value = [sample_github_repo]
                            mock_filter_stars.return_value = [sample_github_repo]
                            
                            languages = ["python", "javascript"]
                            repos = api.get_ai_trending_repositories(languages, max_repos_per_lang=5)
                            
                            assert len(repos) == 2  # 2つの言語から1つずつ
                            assert mock_get_trending.call_count == 2
    
    def test_convert_to_article_format(self, mock_github_instance, sample_github_repo):
        """Article形式変換テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                article = api.convert_to_article_format(sample_github_repo)
                
                assert article["source"] == "github"
                assert sample_github_repo.full_name in article["title"]
                assert article["url"] == sample_github_repo.url
                assert article["score"] == sample_github_repo.stars_count
                assert article["source_specific"]["language"] == "Python"
                assert article["source_specific"]["topics"] == sample_github_repo.topics
    
    def test_get_rate_limit_info(self, mock_github_instance):
        """レート制限情報取得テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                # レート制限情報のモック
                mock_rate_limit = Mock()
                mock_core = Mock()
                mock_core.limit = 5000
                mock_core.remaining = 4500
                mock_core.reset = datetime.now()
                
                mock_search = Mock()
                mock_search.limit = 30
                mock_search.remaining = 25
                mock_search.reset = datetime.now()
                
                mock_rate_limit.core = mock_core
                mock_rate_limit.search = mock_search
                mock_github_instance.get_rate_limit.return_value = mock_rate_limit
                
                api = GitHubTrendingAPI()
                rate_info = api.get_rate_limit_info()
                
                assert rate_info["core"]["limit"] == 5000
                assert rate_info["core"]["remaining"] == 4500
                assert rate_info["search"]["limit"] == 30
                assert rate_info["search"]["remaining"] == 25
    
    def test_get_rate_limit_info_error(self, mock_github_instance):
        """レート制限情報取得エラーテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                mock_github_instance.get_rate_limit.side_effect = Exception("Rate limit API error")
                
                api = GitHubTrendingAPI()
                rate_info = api.get_rate_limit_info()
                
                assert rate_info == {}  # エラー時は空辞書
    
    @patch('time.sleep')
    def test_get_trending_repositories_api_error(self, mock_sleep, mock_github_instance):
        """API エラー時のテスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                mock_github_instance.search_repositories.side_effect = Exception("Search API Error")
                
                api = GitHubTrendingAPI()
                
                with pytest.raises(Exception, match="Search API Error"):
                    api.get_trending_repositories()
    
    @patch('time.sleep')
    def test_get_ai_trending_language_error_handling(self, mock_sleep, mock_github_instance):
        """言語別取得エラー時の継続処理テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                
                with patch.object(api, 'get_trending_repositories') as mock_get_trending:
                    # 最初の言語でエラー、2番目は成功
                    mock_get_trending.side_effect = [Exception("Error"), []]
                    
                    languages = ["badlang", "python"]
                    repos = api.get_ai_trending_repositories(languages)
                    
                    # エラーが発生しても処理が継続される
                    assert isinstance(repos, list)
                    assert mock_get_trending.call_count == 2
    
    def test_deduplication_by_full_name(self, mock_github_instance):
        """full_name重複除去テスト"""
        with patch.dict(os.environ, {'GITHUB_ACCESS_TOKEN': 'test_token'}):
            with patch('github.Github', return_value=mock_github_instance):
                api = GitHubTrendingAPI()
                
                # 同じfull_nameのリポジトリを2つ作成
                repo1 = GitHubRepository(
                    id=1, name="ai-toolkit", full_name="user/ai-toolkit",
                    description="First repo", url="https://github.com/user/ai-toolkit",
                    stars_count=100, today_stars=5, language="Python", topics=[],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                repo2 = GitHubRepository(
                    id=2, name="ai-toolkit", full_name="user/ai-toolkit",
                    description="Duplicate repo", url="https://github.com/user/ai-toolkit",
                    stars_count=80, today_stars=3, language="Python", topics=[],
                    created_at=datetime.now(), updated_at=datetime.now(),
                    pushed_at=datetime.now(), owner="user"
                )
                
                with patch.object(api, 'get_trending_repositories', return_value=[repo1, repo2]):
                    with patch.object(api, 'filter_ai_repositories', side_effect=lambda x: x):
                        with patch.object(api, 'filter_by_stars', side_effect=lambda x, **kwargs: x):
                            
                            repos = api.get_ai_trending_repositories(["python"])
                            
                            # 重複除去により1件のみ残る（Star数が高い方）
                            assert len(repos) == 1
                            assert repos[0].stars_count == 100
