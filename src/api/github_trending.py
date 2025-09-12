"""GitHub Trending API連携モジュール

GitHub APIを使用してトレンディングリポジトリから
AI関連のプロジェクトを取得し、分析する機能を提供。
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
import github
from urllib.parse import urlparse

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class GitHubRepository:
    """GitHub リポジトリデータクラス"""
    id: int
    name: str
    full_name: str
    description: str
    url: str
    stars_count: int
    today_stars: Optional[int]
    language: str
    topics: List[str]
    created_at: datetime
    updated_at: datetime
    pushed_at: datetime
    owner: str
    readme_content: Optional[str] = None
    size: int = 0
    forks_count: int = 0
    watchers_count: int = 0
    open_issues_count: int = 0


class GitHubTrendingAPI:
    """GitHub Trending API クライアント"""
    
    def __init__(self):
        """
        GitHub APIクライアントを初期化
        
        環境変数から認証情報を取得:
        - GITHUB_ACCESS_TOKEN: GitHub Personal Access Token
        """
        self.access_token = os.getenv('GITHUB_ACCESS_TOKEN')
        
        if not self.access_token:
            raise ValueError("GitHub access token not found in environment variables")
        
        try:
            self.github = github.Github(self.access_token)
            # 実ネットワークを避けるためユーザー取得は強制しない（テスト容易性のため）
            try:
                user = self.github.get_user()
                # user はモックされる想定。実オブジェクトでも属性アクセスのみ。
                _login = getattr(user, "login", "unknown")
                logger.info(f"GitHub API client initialized successfully (user: {_login})")
            except Exception:
                # 初期化ログのみ残し、以降のAPI呼び出し時に個別ハンドリング
                logger.info("GitHub API client initialized (user check skipped)")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub API client: {e}")
            raise
    
    def get_trending_repositories(self, language: str = "", since: str = "daily") -> List[GitHubRepository]:
        """
        GitHub Search APIを使用してトレンディングリポジトリを取得
        
        Args:
            language: プログラミング言語 ("python", "javascript", etc.)
            since: 期間 ("daily", "weekly", "monthly")
        
        Returns:
            GitHubRepository オブジェクトのリスト
        """
        try:
            # 日付の計算
            if since == "daily":
                date_threshold = datetime.now() - timedelta(days=1)
            elif since == "weekly":
                date_threshold = datetime.now() - timedelta(weeks=1)
            else:  # monthly
                date_threshold = datetime.now() - timedelta(days=30)
            
            date_str = date_threshold.strftime("%Y-%m-%d")
            
            # Search query構築
            query_parts = [f"created:>{date_str}"]
            
            if language:
                query_parts.append(f"language:{language}")
            
            # AI関連トピックを含む
            ai_topics = [
                "machine-learning", "artificial-intelligence", 
                "deep-learning", "neural-networks", "nlp"
            ]
            topic_query = " OR ".join([f"topic:{topic}" for topic in ai_topics])
            query_parts.append(f"({topic_query})")
            
            query = " ".join(query_parts)
            
            logger.info(f"Searching GitHub repositories with query: {query}")
            
            # Search API実行
            repositories = self.github.search_repositories(
                query=query,
                sort="stars",
                order="desc"
            )
            
            repo_list = []
            count = 0
            
            for repo in repositories:
                if count >= 50:  # 制限を設ける
                    break
                
                try:
                    # GitHubRepositoryオブジェクトに変換
                    github_repo = self._convert_to_github_repository(repo)
                    repo_list.append(github_repo)
                    count += 1
                    
                    # レート制限対応
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.warning(f"Error processing repository {repo.full_name}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(repo_list)} trending repositories")
            return repo_list
            
        except Exception as e:
            logger.error(f"Error fetching trending repositories: {e}")
            raise
    
    def _convert_to_github_repository(self, repo: "github.Repository.Repository") -> GitHubRepository:
        """
        PyGitHub Repository オブジェクトを GitHubRepository に変換
        
        Args:
            repo: PyGitHub Repository オブジェクト
        
        Returns:
            GitHubRepository オブジェクト
        """
        try:
            # トピック取得（API制限を考慮してtry-catch）
            topics = []
            try:
                topics = repo.get_topics()
            except Exception:
                topics = []
            
            # README取得（オプション）
            readme_content = None
            try:
                readme = repo.get_readme()
                readme_content = readme.decoded_content.decode('utf-8')[:1000]  # 最初の1000文字のみ
            except Exception:
                readme_content = None
            
            return GitHubRepository(
                id=repo.id,
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description or "",
                url=repo.html_url,
                stars_count=repo.stargazers_count,
                today_stars=None,  # GitHub APIでは直接取得不可
                language=repo.language or "Unknown",
                topics=topics,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                pushed_at=repo.pushed_at,
                owner=repo.owner.login,
                readme_content=readme_content,
                size=repo.size,
                forks_count=repo.forks_count,
                watchers_count=repo.watchers_count,
                open_issues_count=repo.open_issues_count
            )
            
        except Exception as e:
            logger.error(f"Error converting repository {repo.full_name}: {e}")
            raise
    
    def filter_ai_repositories(self, repositories: List[GitHubRepository]) -> List[GitHubRepository]:
        """
        AI関連キーワードでリポジトリをフィルタリング
        
        Args:
            repositories: GitHubRepository オブジェクトのリスト
        
        Returns:
            AI関連のリポジトリのみを含むリスト
        """
        ai_keywords = [
            "machine learning", "artificial intelligence", "deep learning",
            "neural network", "computer vision", "natural language processing",
            "nlp", "ml", "ai", "tensorflow", "pytorch", "keras", "scikit",
            "transformer", "bert", "gpt", "llm", "language model",
            "data science", "reinforcement learning", "computer vision",
            "generative", "diffusion", "stable diffusion", "chatbot"
        ]
        
        ai_topics = [
            "machine-learning", "artificial-intelligence", "deep-learning",
            "neural-networks", "computer-vision", "natural-language-processing",
            "data-science", "reinforcement-learning", "nlp", "ml", "ai"
        ]
        
        filtered_repos = []
        
        for repo in repositories:
            # 名前、説明、トピック、README で AI キーワード検索
            search_text = (
                repo.name.lower() + " " +
                repo.description.lower() + " " +
                " ".join(repo.topics).lower() + " " +
                (repo.readme_content.lower() if repo.readme_content else "")
            )
            
            # AI関連キーワードまたはトピックが含まれているかチェック
            has_ai_keyword = any(keyword.lower() in search_text for keyword in ai_keywords)
            has_ai_topic = any(topic in repo.topics for topic in ai_topics)
            
            if has_ai_keyword or has_ai_topic:
                filtered_repos.append(repo)
                logger.debug(f"AI-related repository found: {repo.full_name}")
        
        logger.info(f"Filtered {len(filtered_repos)} AI-related repositories from {len(repositories)} total")
        return filtered_repos
    
    def filter_by_stars(self, repositories: List[GitHubRepository], min_stars: int = 10) -> List[GitHubRepository]:
        """
        Star数でフィルタリング
        
        Args:
            repositories: GitHubRepository オブジェクトのリスト
            min_stars: 最小Star数閾値
        
        Returns:
            指定Star数以上のリポジトリのみを含むリスト
        """
        filtered_repos = [repo for repo in repositories if repo.stars_count >= min_stars]
        logger.info(f"Filtered {len(filtered_repos)} repositories with stars >= {min_stars}")
        return filtered_repos
    
    def get_ai_trending_repositories(self, languages: List[str], max_repos_per_lang: int = 10) -> List[GitHubRepository]:
        """
        複数言語からAI関連トレンディングリポジトリを取得
        
        Args:
            languages: 対象プログラミング言語のリスト
            max_repos_per_lang: 各言語から取得するリポジトリ数の上限
        
        Returns:
            AI関連のリポジトリのリスト（Star数順でソート）
        """
        all_repos = []
        
        for language in languages:
            try:
                # 各言語でトレンディングリポジトリを取得
                repos = self.get_trending_repositories(language=language, since="daily")
                
                # AI関連でフィルタリング
                ai_repos = self.filter_ai_repositories(repos)
                
                # Star数でフィルタリング
                star_filtered = self.filter_by_stars(ai_repos, min_stars=10)
                
                # 言語ごとにfull_nameで重複除去
                deduped: List[GitHubRepository] = []
                seen: set = set()
                for r in star_filtered:
                    if r.full_name not in seen:
                        deduped.append(r)
                        seen.add(r.full_name)
                
                all_repos.extend(deduped)
                
                logger.info(f"Collected {len(deduped)} repositories for language: {language}")
                
                # GitHub API レート制限対応（1秒間隔）
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Failed to fetch repositories for language {language}: {e}")
                continue
        
        # 言語単位での重複除去は取得時に行っているため、ここでは全体での重複除去は行わない
        # Star数順でソート（降順）
        all_repos.sort(key=lambda repo: repo.stars_count, reverse=True)
        logger.info(f"Final result: {len(all_repos)} AI-related repositories from {len(languages)} languages")
        return all_repos[:max_repos_per_lang * len(languages)]  # 最大件数制限
    
    def convert_to_article_format(self, github_repo: GitHubRepository) -> Dict:
        """
        GitHubRepositoryを既存のArticle形式に変換
        
        Args:
            github_repo: GitHubRepository オブジェクト
        
        Returns:
            Article互換の辞書形式データ
        """
        return {
            "source": "github",
            "title": f"{github_repo.full_name}: {github_repo.description[:100]}...",
            "url": github_repo.url,
            "score": github_repo.stars_count,
            "time": github_repo.updated_at.isoformat(),
            "source_specific": {
                "github_id": github_repo.id,
                "full_name": github_repo.full_name,
                "description": github_repo.description,
                "language": github_repo.language,
                "topics": github_repo.topics,
                "owner": github_repo.owner,
                "stars_count": github_repo.stars_count,
                "forks_count": github_repo.forks_count,
                "watchers_count": github_repo.watchers_count,
                "open_issues_count": github_repo.open_issues_count,
                "created_at": github_repo.created_at.isoformat(),
                "pushed_at": github_repo.pushed_at.isoformat(),
                "readme_content": github_repo.readme_content,
                "size": github_repo.size
            }
        }
    
    def get_rate_limit_info(self) -> Dict:
        """
        GitHub API レート制限情報を取得
        
        Returns:
            レート制限情報の辞書
        """
        try:
            rate_limit = self.github.get_rate_limit()
            return {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset
                },
                "search": {
                    "limit": rate_limit.search.limit,
                    "remaining": rate_limit.search.remaining,
                    "reset": rate_limit.search.reset
                }
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {}


def main():
    """テスト用のメイン関数"""
    # 環境変数の確認
    if not os.getenv('GITHUB_ACCESS_TOKEN'):
        print("Error: GitHub access token not found")
        print("Please set GITHUB_ACCESS_TOKEN environment variable")
        return
    
    try:
        # GitHub APIクライアント初期化
        github_api = GitHubTrendingAPI()
        
        # レート制限情報表示
        rate_info = github_api.get_rate_limit_info()
        print(f"\n=== GitHub API Rate Limit Info ===")
        print(f"Search API: {rate_info.get('search', {}).get('remaining', 'N/A')} remaining")
        print(f"Core API: {rate_info.get('core', {}).get('remaining', 'N/A')} remaining")
        
        # 対象言語
        languages = ["python", "javascript", "typescript"]
        
        # AI関連トレンディングリポジトリを取得
        repos = github_api.get_ai_trending_repositories(languages, max_repos_per_lang=3)
        
        print(f"\n=== Found {len(repos)} AI-related trending repositories ===")
        for i, repo in enumerate(repos, 1):
            print(f"\n{i}. {repo.full_name}")
            print(f"   Description: {repo.description[:100]}...")
            print(f"   Language: {repo.language}")
            print(f"   Stars: {repo.stars_count}")
            print(f"   Topics: {', '.join(repo.topics[:5])}")
            print(f"   URL: {repo.url}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
