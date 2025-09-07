"""記事重複除去モジュール

複数のニュースソースから収集された記事の重複を検出・除去する機能を提供。
URLの正規化、タイトルの類似度、内容の類似度などを考慮した高精度な重複除去を実現。
"""

import re
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse, parse_qs
import difflib
from dataclasses import dataclass

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class DuplicationScore:
    """重複スコアデータクラス"""
    url_similarity: float
    title_similarity: float
    content_similarity: float
    overall_score: float
    is_duplicate: bool


class ArticleDeduplicator:
    """記事重複除去クラス
    
    複数の手法を組み合わせて記事の重複を検出し、
    より情報量の多い記事を優先的に残す。
    """
    
    def __init__(self, 
                 url_threshold: float = 0.8,
                 title_threshold: float = 0.85,
                 overall_threshold: float = 0.7):
        """
        重複除去器を初期化
        
        Args:
            url_threshold: URL類似度の閾値
            title_threshold: タイトル類似度の閾値  
            overall_threshold: 総合類似度の閾値
        """
        self.url_threshold = url_threshold
        self.title_threshold = title_threshold
        self.overall_threshold = overall_threshold
        self.logger = setup_logger(__name__)
    
    def normalize_url(self, url: str) -> str:
        """
        URLを正規化して比較しやすくする
        
        Args:
            url: 正規化するURL
        
        Returns:
            str: 正規化されたURL
        """
        try:
            # URLをパース
            parsed = urlparse(url.lower().strip())
            
            # スキームを統一（httpをhttpsに）
            scheme = "https" if parsed.scheme in ["http", "https"] else parsed.scheme
            
            # ホスト名から www. を除去
            netloc = parsed.netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]
            
            # 不要なクエリパラメータを除去
            ignore_params = {
                "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                "fbclid", "gclid", "ref", "referrer", "_source", "source"
            }
            
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items() 
                if k not in ignore_params
            }
            
            # パスから末尾のスラッシュを除去
            path = parsed.path.rstrip("/")
            
            # 正規化されたURLを構築
            normalized = f"{scheme}://{netloc}{path}"
            
            # クエリパラメータがあれば追加
            if filtered_params:
                query_string = "&".join([
                    f"{k}={v[0]}" for k, v in filtered_params.items()
                ])
                normalized += f"?{query_string}"
            
            return normalized
            
        except Exception as e:
            self.logger.warning(f"Failed to normalize URL '{url}': {e}")
            return url.lower().strip()
    
    def calculate_url_similarity(self, url1: str, url2: str) -> float:
        """
        2つのURL間の類似度を計算
        
        Args:
            url1: 1つ目のURL
            url2: 2つ目のURL
        
        Returns:
            float: 類似度スコア（0.0-1.0）
        """
        try:
            normalized1 = self.normalize_url(url1)
            normalized2 = self.normalize_url(url2)
            
            # 完全一致
            if normalized1 == normalized2:
                return 1.0
            
            # ドメインが異なる場合は低スコア
            domain1 = urlparse(normalized1).netloc
            domain2 = urlparse(normalized2).netloc
            
            if domain1 != domain2:
                return 0.0
            
            # パス部分の類似度を計算
            path1 = urlparse(normalized1).path
            path2 = urlparse(normalized2).path
            
            # 文字列類似度を使用
            similarity = difflib.SequenceMatcher(None, path1, path2).ratio()
            
            return similarity
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate URL similarity: {e}")
            return 0.0
    
    def normalize_title(self, title: str) -> str:
        """
        タイトルを正規化して比較しやすくする
        
        Args:
            title: 正規化するタイトル
        
        Returns:
            str: 正規化されたタイトル
        """
        # 小文字化
        normalized = title.lower().strip()
        
        # 特殊文字・記号の除去
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # 複数の空白を単一の空白に
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # 一般的な接頭辞・接尾辞の除去
        prefixes_to_remove = [
            "show hn", "ask hn", "tell hn", 
            "breaking", "urgent", "update",
            "new", "latest", "just in"
        ]
        
        suffixes_to_remove = [
            "hacker news", "hn", "reddit", "github",
            "discussion", "comments", "thread"
        ]
        
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if normalized.endswith(" " + suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        return normalized
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        2つのタイトル間の類似度を計算
        
        Args:
            title1: 1つ目のタイトル
            title2: 2つ目のタイトル
        
        Returns:
            float: 類似度スコア（0.0-1.0）
        """
        try:
            normalized1 = self.normalize_title(title1)
            normalized2 = self.normalize_title(title2)
            
            # 完全一致
            if normalized1 == normalized2:
                return 1.0
            
            # 文字列類似度
            char_similarity = difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
            
            # 単語レベルの類似度
            words1 = set(normalized1.split())
            words2 = set(normalized2.split())
            
            if not words1 or not words2:
                return char_similarity
            
            # Jaccard係数（共通単語の割合）
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            jaccard = len(intersection) / len(union)
            
            # 文字列類似度と単語類似度の重み付き平均
            combined_similarity = (char_similarity * 0.6) + (jaccard * 0.4)
            
            return combined_similarity
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate title similarity: {e}")
            return 0.0
    
    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        2つのコンテンツ間の類似度を計算
        
        Args:
            content1: 1つ目のコンテンツ
            content2: 2つ目のコンテンツ
        
        Returns:
            float: 類似度スコア（0.0-1.0）
        """
        try:
            if not content1 or not content2:
                return 0.0
            
            # 正規化
            normalized1 = re.sub(r'\s+', ' ', content1.lower().strip())
            normalized2 = re.sub(r'\s+', ' ', content2.lower().strip())
            
            # 短いコンテンツの場合は文字列類似度のみ
            if len(normalized1) < 50 or len(normalized2) < 50:
                return difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
            
            # 長いコンテンツの場合は文の先頭部分で比較
            prefix1 = normalized1[:200]
            prefix2 = normalized2[:200]
            
            similarity = difflib.SequenceMatcher(None, prefix1, prefix2).ratio()
            
            return similarity
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate content similarity: {e}")
            return 0.0
    
    def calculate_duplication_score(self, article1: Dict, article2: Dict) -> DuplicationScore:
        """
        2つの記事間の重複スコアを計算
        
        Args:
            article1: 1つ目の記事
            article2: 2つ目の記事
        
        Returns:
            DuplicationScore: 重複スコア詳細
        """
        try:
            # URL類似度
            url1 = article1.get("url", "")
            url2 = article2.get("url", "")
            url_sim = self.calculate_url_similarity(url1, url2)
            
            # タイトル類似度
            title1 = article1.get("title", "")
            title2 = article2.get("title", "")
            title_sim = self.calculate_title_similarity(title1, title2)
            
            # コンテンツ類似度
            content1 = article1.get("content", "")
            content2 = article2.get("content", "")
            content_sim = self.calculate_content_similarity(content1, content2)
            
            # 総合スコア計算（重み付き平均）
            overall_score = (url_sim * 0.5) + (title_sim * 0.4) + (content_sim * 0.1)
            
            # 重複判定
            is_duplicate = (
                url_sim >= self.url_threshold or
                title_sim >= self.title_threshold or
                overall_score >= self.overall_threshold
            )
            
            return DuplicationScore(
                url_similarity=url_sim,
                title_similarity=title_sim,
                content_similarity=content_sim,
                overall_score=overall_score,
                is_duplicate=is_duplicate
            )
            
        except Exception as e:
            self.logger.error(f"Failed to calculate duplication score: {e}")
            return DuplicationScore(0.0, 0.0, 0.0, 0.0, False)
    
    def choose_better_article(self, article1: Dict, article2: Dict) -> Dict:
        """
        2つの重複記事のうち、より良い記事を選択
        
        選択基準:
        1. より詳細な情報を持つ記事
        2. より信頼性の高いソース
        3. より高いスコア
        
        Args:
            article1: 1つ目の記事
            article2: 2つ目の記事
        
        Returns:
            Dict: 選択された記事
        """
        try:
            score1 = 0
            score2 = 0
            
            # ソースの優先度（既存システムとの互換性を考慮）
            source_priority = {
                "hackernews": 3,
                "github": 2,
                "reddit": 1
            }
            
            source1 = article1.get("source", "unknown")
            source2 = article2.get("source", "unknown")
            
            score1 += source_priority.get(source1, 0)
            score2 += source_priority.get(source2, 0)
            
            # 記事スコア（いいね数、Star数など）
            article_score1 = article1.get("score", 0)
            article_score2 = article2.get("score", 0)
            
            if article_score1 > article_score2:
                score1 += 2
            elif article_score2 > article_score1:
                score2 += 2
            
            # コンテンツの充実度
            content1_length = len(article1.get("content", ""))
            content2_length = len(article2.get("content", ""))
            
            if content1_length > content2_length:
                score1 += 1
            elif content2_length > content1_length:
                score2 += 1
            
            # source_specific情報の充実度
            specific1 = article1.get("source_specific", {})
            specific2 = article2.get("source_specific", {})
            
            if len(specific1) > len(specific2):
                score1 += 1
            elif len(specific2) > len(specific1):
                score2 += 1
            
            # より良い記事を選択
            if score1 >= score2:
                chosen = article1
                discarded = article2
            else:
                chosen = article2
                discarded = article1
            
            self.logger.debug(f"Chose article from {chosen.get('source')} over {discarded.get('source')} "
                            f"(scores: {score1} vs {score2})")
            
            return chosen
            
        except Exception as e:
            self.logger.error(f"Failed to choose better article: {e}")
            # エラー時は最初の記事を返す
            return article1
    
    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """
        記事リストから重複を除去
        
        Args:
            articles: 記事のリスト
        
        Returns:
            List[Dict]: 重複除去後の記事リスト
        """
        if not articles:
            return []
        
        self.logger.info(f"Starting deduplication for {len(articles)} articles")
        
        unique_articles = []
        duplicate_count = 0
        
        for i, current_article in enumerate(articles):
            is_duplicate = False
            
            # 既存のユニーク記事と比較
            for j, existing_article in enumerate(unique_articles):
                try:
                    score = self.calculate_duplication_score(current_article, existing_article)
                    
                    if score.is_duplicate:
                        # 重複発見 - より良い記事を選択
                        better_article = self.choose_better_article(current_article, existing_article)
                        unique_articles[j] = better_article
                        
                        is_duplicate = True
                        duplicate_count += 1
                        
                        self.logger.debug(f"Duplicate found: '{current_article.get('title', '')[:50]}...' "
                                        f"(similarity: {score.overall_score:.3f})")
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error comparing articles {i} and {j}: {e}")
                    continue
            
            # 重複でない場合は追加
            if not is_duplicate:
                unique_articles.append(current_article)
        
        self.logger.info(f"Deduplication completed: {len(unique_articles)} unique articles "
                        f"({duplicate_count} duplicates removed)")
        
        return unique_articles
    
    def get_statistics(self, articles: List[Dict]) -> Dict[str, any]:
        """
        重複除去の統計情報を取得
        
        Args:
            articles: 記事のリスト
        
        Returns:
            Dict: 統計情報
        """
        unique_articles = self.remove_duplicates(articles)
        
        total_count = len(articles)
        unique_count = len(unique_articles)
        duplicate_count = total_count - unique_count
        
        # ソース別統計
        source_stats = {}
        for article in articles:
            source = article.get("source", "unknown")
            source_stats[source] = source_stats.get(source, 0) + 1
        
        unique_source_stats = {}
        for article in unique_articles:
            source = article.get("source", "unknown")
            unique_source_stats[source] = unique_source_stats.get(source, 0) + 1
        
        return {
            "total_articles": total_count,
            "unique_articles": unique_count,
            "duplicates_removed": duplicate_count,
            "duplication_rate": (duplicate_count / max(total_count, 1)) * 100,
            "source_distribution": source_stats,
            "unique_source_distribution": unique_source_stats
        }


def main():
    """テスト用のメイン関数"""
    # サンプル記事でテスト
    sample_articles = [
        {
            "source": "hackernews",
            "title": "OpenAI Releases GPT-4 Turbo",
            "url": "https://openai.com/blog/gpt-4-turbo",
            "score": 150,
            "content": "OpenAI has announced the release of GPT-4 Turbo..."
        },
        {
            "source": "reddit",
            "title": "OpenAI releases GPT-4 Turbo - Discussion",
            "url": "https://www.openai.com/blog/gpt-4-turbo?utm_source=reddit",
            "score": 85,
            "content": "OpenAI announced GPT-4 Turbo today..."
        },
        {
            "source": "github",
            "title": "New Machine Learning Framework Released",
            "url": "https://github.com/example/ml-framework",
            "score": 200,
            "content": "A new framework for machine learning applications..."
        }
    ]
    
    deduplicator = ArticleDeduplicator()
    
    print("=== Original Articles ===")
    for i, article in enumerate(sample_articles):
        print(f"{i+1}. [{article['source']}] {article['title']}")
    
    print("\n=== After Deduplication ===")
    unique_articles = deduplicator.remove_duplicates(sample_articles)
    for i, article in enumerate(unique_articles):
        print(f"{i+1}. [{article['source']}] {article['title']}")
    
    print("\n=== Statistics ===")
    stats = deduplicator.get_statistics(sample_articles)
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
