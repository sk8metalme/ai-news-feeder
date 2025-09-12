"""ニュースオーケストレーター

複数のニュースソース（Hacker News, Reddit, GitHub Trending）からの
データ収集と統合処理を管理するモジュール。
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..api.hacker_news import HackerNewsAPI
from ..api.reddit_api import RedditAPI
from ..api.github_trending import GitHubTrendingAPI
from ..verification.fact_checker import FactChecker
from ..notification.slack_notifier import SlackNotifier
from ..utils.logger import setup_logger
from config.settings import (
    ENABLE_REDDIT,
    ENABLE_GITHUB,
    MAX_ARTICLES_PER_SOURCE,
    CHECK_INTERVAL_HOURS,
    NOTIFY_VERIFICATION_LEVEL,
)
from ..utils.deduplication import ArticleDeduplicator
from ..utils.unified_report_generator import UnifiedReportGenerator

logger = setup_logger(__name__)


@dataclass
class SourceConfig:
    """ソース設定データクラス"""
    enabled: bool
    max_articles: int
    timeout: int = 300  # 5分


@dataclass
class OrchestrationResult:
    """オーケストレーション結果データクラス"""
    total_articles_collected: int
    articles_by_source: Dict[str, int]
    articles_verified: int
    articles_summarized: int
    articles_notified: int
    processing_time: float
    errors: List[str]
    warnings: List[str]


class NewsOrchestrator:
    """ニュースオーケストレーター
    
    複数のニュースソースからの並列データ収集、
    統合処理、検証、通知を統括管理する。
    """
    
    def __init__(self):
        """オーケストレーターを初期化"""
        self.logger = setup_logger(__name__)
        
        # 各種APIクライアントの初期化
        self.hacker_news_api = None
        self.reddit_api = None
        self.github_api = None
        self.fact_checker = None
        self.slack_notifier = None
        
        # ユーティリティ
        self.deduplicator = ArticleDeduplicator()
        self.report_generator = UnifiedReportGenerator()
        
        # 設定（.env から）
        self.source_configs = {
            "hackernews": SourceConfig(enabled=True, max_articles=MAX_ARTICLES_PER_SOURCE),
            "reddit": SourceConfig(enabled=ENABLE_REDDIT, max_articles=MAX_ARTICLES_PER_SOURCE),
            "github": SourceConfig(enabled=ENABLE_GITHUB, max_articles=MAX_ARTICLES_PER_SOURCE),
        }
        
        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "articles_processed": 0
        }
    
    def initialize_sources(self) -> bool:
        """
        各ニュースソースのAPIクライアントを初期化
        
        Returns:
            bool: 初期化成功の可否
        """
        try:
            # Hacker News API（常に利用可能）
            from ..api.hacker_news import HackerNewsAPI
            self.hacker_news_api = HackerNewsAPI()
            self.logger.info("Hacker News API initialized")
            
            # Reddit API（オプション）
            if self.source_configs["reddit"].enabled:
                try:
                    self.reddit_api = RedditAPI()
                    self.logger.info("Reddit API initialized")
                except Exception as e:
                    self.logger.warning(f"Reddit API initialization failed: {e}")
                    self.source_configs["reddit"].enabled = False
            
            # GitHub API（オプション）
            if self.source_configs["github"].enabled:
                try:
                    self.github_api = GitHubTrendingAPI()
                    self.logger.info("GitHub API initialized")
                except Exception as e:
                    self.logger.warning(f"GitHub API initialization failed: {e}")
                    self.source_configs["github"].enabled = False
            
            # ファクトチェッカー（設定に従って要約を有効/無効）
            from config import settings as _settings
            self.fact_checker = FactChecker(enable_summarization=_settings.ENABLE_SUMMARIZATION)
            
            # Slack通知
            self.slack_notifier = SlackNotifier()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sources: {e}")
            return False
    
    def collect_from_hackernews(self) -> List[Dict]:
        """Hacker Newsから記事を収集"""
        try:
            self.logger.info("Collecting articles from Hacker News...")
            # AI関連のストーリーを取得
            articles = self.hacker_news_api.get_ai_stories(
                max_stories=self.source_configs["hackernews"].max_articles * 2,
                hours=CHECK_INTERVAL_HOURS,
            )

            # 既存のArticle形式に合わせて変換
            converted_articles = []
            for article in articles:
                converted_articles.append(
                    {
                        "source": "hackernews",
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "score": article.get("score", 0),
                        "time": article.get("time", ""),
                        "source_specific": {
                            "id": article.get("id", ""),
                            "descendants": article.get("descendants", 0),
                            "by": article.get("by", ""),
                        },
                    }
                )
            
            self.logger.info(f"Collected {len(converted_articles)} articles from Hacker News")
            return converted_articles[:self.source_configs["hackernews"].max_articles]
            
        except Exception as e:
            self.logger.error(f"Error collecting from Hacker News: {e}")
            return []
    
    def collect_from_reddit(self) -> List[Dict]:
        """Redditから記事を収集"""
        if not self.reddit_api or not self.source_configs["reddit"].enabled:
            return []
        
        try:
            self.logger.info("Collecting articles from Reddit...")
            
            subreddits = ["MachineLearning", "artificial", "singularity", "MachineLearningNews"]
            reddit_posts = self.reddit_api.get_ai_news_from_subreddits(
                subreddits, 
                max_posts_per_sub=2
            )
            
            # Article形式に変換
            articles = []
            for post in reddit_posts:
                article = self.reddit_api.convert_to_article_format(post)
                articles.append(article)
            
            self.logger.info(f"Collected {len(articles)} articles from Reddit")
            return articles[:self.source_configs["reddit"].max_articles]
            
        except Exception as e:
            self.logger.error(f"Error collecting from Reddit: {e}")
            return []
    
    def collect_from_github(self) -> List[Dict]:
        """GitHub Trendingから記事を収集"""
        if not self.github_api or not self.source_configs["github"].enabled:
            return []
        
        try:
            self.logger.info("Collecting repositories from GitHub Trending...")
            
            languages = ["python", "javascript", "typescript"]
            github_repos = self.github_api.get_ai_trending_repositories(
                languages,
                max_repos_per_lang=2
            )
            
            # Article形式に変換
            articles = []
            for repo in github_repos:
                article = self.github_api.convert_to_article_format(repo)
                articles.append(article)
            
            self.logger.info(f"Collected {len(articles)} repositories from GitHub Trending")
            return articles[:self.source_configs["github"].max_articles]
            
        except Exception as e:
            self.logger.error(f"Error collecting from GitHub: {e}")
            return []
    
    def collect_all_articles(self) -> List[Dict]:
        """
        全ソースから並列で記事を収集
        
        Returns:
            List[Dict]: 収集された全記事のリスト
        """
        all_articles = []
        collection_functions = []
        
        # 有効なソースの収集関数を準備
        if self.source_configs["hackernews"].enabled:
            collection_functions.append(("hackernews", self.collect_from_hackernews))
        
        if self.source_configs["reddit"].enabled:
            collection_functions.append(("reddit", self.collect_from_reddit))
        
        if self.source_configs["github"].enabled:
            collection_functions.append(("github", self.collect_from_github))
        
        # 並列実行
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 各ソースの収集タスクを送信
            future_to_source = {
                executor.submit(func): source_name 
                for source_name, func in collection_functions
            }
            
            # 結果を収集
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    articles = future.result(timeout=300)  # 5分タイムアウト
                    all_articles.extend(articles)
                    self.logger.info(f"Successfully collected {len(articles)} articles from {source_name}")
                except Exception as e:
                    self.logger.error(f"Error collecting from {source_name}: {e}")
        
        self.logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles
    
    def process_articles(self, articles: List[Dict]) -> OrchestrationResult:
        """
        収集された記事を処理（重複除去、検証、要約、通知）
        
        Args:
            articles: 収集された記事のリスト
        
        Returns:
            OrchestrationResult: 処理結果
        """
        start_time = time.time()
        result = OrchestrationResult(
            total_articles_collected=len(articles),
            articles_by_source={},
            articles_verified=0,
            articles_summarized=0,
            articles_notified=0,
            processing_time=0,
            errors=[],
            warnings=[]
        )
        
        try:
            # ソース別記事数を集計
            for article in articles:
                source = article.get("source", "unknown")
                result.articles_by_source[source] = result.articles_by_source.get(source, 0) + 1
            
            # 重複除去
            self.logger.info("Removing duplicate articles...")
            unique_articles = self.deduplicator.remove_duplicates(articles)
            self.logger.info(f"After deduplication: {len(unique_articles)} unique articles")
            
            # 記事検証・要約・通知
            for article in unique_articles:
                try:
                    # ファクトチェック
                    if self.fact_checker:
                        verification_result = self.fact_checker.verify_article(
                            article.get("title", ""), article.get("url", "")
                        )

                        status = verification_result.get("verification_status")

                        def _should_notify(st: str) -> bool:
                            if NOTIFY_VERIFICATION_LEVEL == "verified_only":
                                return st == "verified"
                            if NOTIFY_VERIFICATION_LEVEL in ("verified_or_partial", "verified_partial"):
                                return st in ("verified", "partially_verified")
                            return True  # all

                        if status == "verified":
                            result.articles_verified += 1
                            
                            # 要約が含まれている場合
                            if verification_result.get("summary"):
                                result.articles_summarized += 1
                            
                        # Slack通知（設定に応じて送信）
                        if self.slack_notifier and _should_notify(status):
                            try:
                                enriched_result = verification_result.copy()
                                enriched_result["source"] = article.get("source", "unknown")
                                enriched_result["source_specific"] = article.get("source_specific", {})
                                self.slack_notifier.send_verification_report(enriched_result)
                                result.articles_notified += 1
                            except Exception as e:
                                error_msg = f"Notification failed for article: {e}"
                                result.errors.append(error_msg)
                                self.logger.error(error_msg)
                        if status != "verified":
                            warning_msg = f"Article not verified: {article.get('title', 'Unknown')[:50]}"
                            result.warnings.append(warning_msg)
                            self.logger.warning(warning_msg)
                    
                except Exception as e:
                    error_msg = f"Error processing article '{article.get('title', 'Unknown')[:50]}': {e}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg)
            
            # 統合レポート生成
            try:
                report_data = {
                    "orchestration_result": result,
                    "articles": unique_articles,
                    "timestamp": datetime.now().isoformat()
                }
                self.report_generator.generate_unified_report(report_data)
            except Exception as e:
                error_msg = f"Report generation failed: {e}"
                result.errors.append(error_msg)
                self.logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Critical error in article processing: {e}"
            result.errors.append(error_msg)
            self.logger.error(error_msg)
        
        # 処理時間を記録
        result.processing_time = time.time() - start_time
        
        # 統計更新
        self.stats["total_runs"] += 1
        if not result.errors:
            self.stats["successful_runs"] += 1
        else:
            self.stats["failed_runs"] += 1
        self.stats["articles_processed"] += result.total_articles_collected
        
        return result
    
    def run_full_orchestration(self) -> OrchestrationResult:
        """
        完全なオーケストレーション実行
        
        Returns:
            OrchestrationResult: 実行結果
        """
        self.logger.info("Starting full news orchestration...")
        
        # ソース初期化
        if not self.initialize_sources():
            return OrchestrationResult(
                total_articles_collected=0,
                articles_by_source={},
                articles_verified=0,
                articles_summarized=0,
                articles_notified=0,
                processing_time=0,
                errors=["Failed to initialize news sources"],
                warnings=[]
            )
        
        # 記事収集
        articles = self.collect_all_articles()
        
        # 記事処理
        result = self.process_articles(articles)
        
        # 結果サマリーをログ出力
        self.logger.info(f"""
Orchestration completed:
- Total articles collected: {result.total_articles_collected}
- Articles by source: {result.articles_by_source}
- Articles verified: {result.articles_verified}
- Articles summarized: {result.articles_summarized}
- Articles notified: {result.articles_notified}
- Processing time: {result.processing_time:.2f}s
- Errors: {len(result.errors)}
- Warnings: {len(result.warnings)}
        """)
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            "success_rate": (self.stats["successful_runs"] / max(self.stats["total_runs"], 1)) * 100,
            "avg_articles_per_run": self.stats["articles_processed"] / max(self.stats["total_runs"], 1)
        }


def main():
    """テスト用のメイン関数"""
    import os
    
    # 必要な環境変数のチェック
    required_env_vars = ["SLACK_WEBHOOK_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please set up your environment variables before running.")
        return
    
    try:
        # オーケストレーター初期化・実行
        orchestrator = NewsOrchestrator()
        result = orchestrator.run_full_orchestration()
        
        # 結果表示
        print(f"\n=== Orchestration Results ===")
        print(f"Total articles: {result.total_articles_collected}")
        print(f"By source: {result.articles_by_source}")
        print(f"Verified: {result.articles_verified}")
        print(f"Summarized: {result.articles_summarized}")
        print(f"Notified: {result.articles_notified}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        # 統計情報
        stats = orchestrator.get_statistics()
        print(f"\n=== Statistics ===")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Avg articles per run: {stats['avg_articles_per_run']:.1f}")
        
    except Exception as e:
        print(f"Orchestration failed: {e}")


if __name__ == "__main__":
    main()
