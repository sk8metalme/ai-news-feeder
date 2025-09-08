"""統合レポート生成モジュール

複数ソースからの記事収集・処理結果を統合し、
詳細な分析レポートをJSON形式で生成する機能を提供。
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import statistics

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class UnifiedReportGenerator:
    """統合レポート生成クラス
    
    複数のニュースソースからの収集結果、処理統計、
    パフォーマンス指標などを統合したレポートを生成。
    """
    
    def __init__(self, output_dir: str = "data"):
        """
        レポート生成器を初期化
        
        Args:
            output_dir: レポート出力ディレクトリ
        """
        self.output_dir = output_dir
        self.logger = setup_logger(__name__)
        
        # 出力ディレクトリを作成
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_unified_report(self, data: Dict[str, Any]) -> str:
        """
        統合レポートを生成
        
        Args:
            data: レポートデータ（orchestration_result, articles, etc.）
        
        Returns:
            str: 生成されたレポートファイルのパス
        """
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y%m%d")
            
            # レポートファイル名
            report_filename = f"unified_ai_news_report_{date_str}.json"
            report_path = os.path.join(self.output_dir, report_filename)
            
            # 統合レポートデータを構築
            report_data = self._build_report_structure(data, timestamp)
            
            # JSONファイルに保存
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Unified report generated: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate unified report: {e}")
            raise
    
    def _build_report_structure(self, data: Dict[str, Any], timestamp: datetime) -> Dict[str, Any]:
        """
        レポートの構造化データを構築
        
        Args:
            data: 入力データ
            timestamp: レポート生成時刻
        
        Returns:
            Dict: 構造化されたレポートデータ
        """
        orchestration_result = data.get("orchestration_result")
        articles = data.get("articles", [])
        
        return {
            "metadata": self._generate_metadata(timestamp),
            "summary": self._generate_summary(orchestration_result),
            "source_analysis": self._analyze_sources(orchestration_result, articles),
            "article_details": self._process_article_details(articles),
            "performance_metrics": self._calculate_performance_metrics(orchestration_result),
            "quality_assessment": self._assess_quality(orchestration_result, articles),
            "trend_analysis": self._analyze_trends(articles),
            "recommendations": self._generate_recommendations(orchestration_result, articles),
            "raw_data": {
                "orchestration_result": self._serialize_orchestration_result(orchestration_result),
                "total_articles": len(articles)
            }
        }
    
    def _generate_metadata(self, timestamp: datetime) -> Dict[str, Any]:
        """メタデータ生成"""
        return {
            "report_version": "1.0.0",
            "generated_at": timestamp.isoformat(),
            "report_type": "unified_multi_source",
            "sources_included": ["hackernews", "reddit", "github"],
            "timezone": "JST",
            "generator": "AI News Feeder v1.3.0"
        }
    
    def _generate_summary(self, orchestration_result) -> Dict[str, Any]:
        """サマリー情報生成"""
        if not orchestration_result:
            return {"status": "no_data"}
        
        return {
            "execution_status": "success" if not orchestration_result.errors else "partial_success",
            "total_articles_collected": orchestration_result.total_articles_collected,
            "articles_verified": orchestration_result.articles_verified,
            "articles_summarized": orchestration_result.articles_summarized,
            "articles_notified": orchestration_result.articles_notified,
            "processing_time_seconds": round(orchestration_result.processing_time, 2),
            "error_count": len(orchestration_result.errors),
            "warning_count": len(orchestration_result.warnings),
            "success_rate": round(
                (orchestration_result.articles_notified / max(orchestration_result.total_articles_collected, 1)) * 100, 
                2
            )
        }
    
    def _analyze_sources(self, orchestration_result, articles: List[Dict]) -> Dict[str, Any]:
        """ソース別分析"""
        if not orchestration_result:
            return {}
        
        source_analysis = {}
        
        # ソース別記事数
        for source, count in orchestration_result.articles_by_source.items():
            source_analysis[source] = {
                "articles_collected": count,
                "collection_enabled": True,
                "avg_score": 0,
                "articles": []
            }
        
        # 各記事をソース別に分類・分析
        for article in articles:
            source = article.get("source", "unknown")
            if source in source_analysis:
                source_analysis[source]["articles"].append({
                    "title": article.get("title", "")[:100],
                    "score": article.get("score", 0),
                    "url": article.get("url", "")
                })
        
        # ソース別平均スコア計算
        for source, info in source_analysis.items():
            if info["articles"]:
                scores = [article["score"] for article in info["articles"]]
                info["avg_score"] = round(statistics.mean(scores), 2)
                info["max_score"] = max(scores)
                info["min_score"] = min(scores)
        
        return source_analysis
    
    def _process_article_details(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """記事詳細処理"""
        processed_articles = []
        
        for article in articles:
            processed_article = {
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "score": article.get("score", 0),
                "timestamp": article.get("time", ""),
                "content_length": len(article.get("content", "")),
                "source_specific_data": article.get("source_specific", {}),
                "processing_notes": []
            }
            
            # ソース固有の分析
            source = article.get("source", "")
            if source == "reddit":
                specific = article.get("source_specific", {})
                processed_article["reddit_data"] = {
                    "subreddit": specific.get("subreddit", ""),
                    "author": specific.get("author", ""),
                    "num_comments": specific.get("num_comments", 0),
                    "flair_text": specific.get("flair_text", "")
                }
            elif source == "github":
                specific = article.get("source_specific", {})
                processed_article["github_data"] = {
                    "language": specific.get("language", ""),
                    "topics": specific.get("topics", []),
                    "forks_count": specific.get("forks_count", 0),
                    "open_issues_count": specific.get("open_issues_count", 0)
                }
            elif source == "hackernews":
                specific = article.get("source_specific", {})
                processed_article["hackernews_data"] = {
                    "item_id": specific.get("id", ""),
                    "descendants": specific.get("descendants", 0),
                    "by": specific.get("by", "")
                }
            
            processed_articles.append(processed_article)
        
        return processed_articles
    
    def _calculate_performance_metrics(self, orchestration_result) -> Dict[str, Any]:
        """パフォーマンス指標計算"""
        if not orchestration_result:
            return {}
        
        total_articles = orchestration_result.total_articles_collected
        processing_time = orchestration_result.processing_time
        
        return {
            "total_processing_time": round(processing_time, 2),
            "articles_per_second": round(total_articles / max(processing_time, 0.1), 2),
            "avg_time_per_article": round(processing_time / max(total_articles, 1), 2),
            "verification_rate": round(
                (orchestration_result.articles_verified / max(total_articles, 1)) * 100, 2
            ),
            "summarization_rate": round(
                (orchestration_result.articles_summarized / max(total_articles, 1)) * 100, 2
            ),
            "notification_success_rate": round(
                (orchestration_result.articles_notified / max(orchestration_result.articles_verified, 1)) * 100, 2
            )
        }
    
    def _assess_quality(self, orchestration_result, articles: List[Dict]) -> Dict[str, Any]:
        """品質評価"""
        if not articles:
            return {"overall_quality": "no_data"}
        
        # 記事品質の基本指標
        scores = [article.get("score", 0) for article in articles]
        title_lengths = [len(article.get("title", "")) for article in articles]
        content_lengths = [len(article.get("content", "")) for article in articles]
        
        quality_assessment = {
            "overall_quality": "good",  # デフォルト
            "score_statistics": {
                "avg": round(statistics.mean(scores), 2) if scores else 0,
                "median": round(statistics.median(scores), 2) if scores else 0,
                "max": max(scores) if scores else 0,
                "min": min(scores) if scores else 0
            },
            "content_quality": {
                "avg_title_length": round(statistics.mean(title_lengths), 2) if title_lengths else 0,
                "avg_content_length": round(statistics.mean(content_lengths), 2) if content_lengths else 0,
                "articles_with_content": len([a for a in articles if a.get("content", "")])
            },
            "source_diversity": len(set(article.get("source", "") for article in articles)),
            "potential_issues": []
        }
        
        # 品質問題の検出
        if statistics.mean(scores) < 50:
            quality_assessment["potential_issues"].append("Low average article scores")
        
        if len([a for a in articles if not a.get("content", "")]) > len(articles) * 0.5:
            quality_assessment["potential_issues"].append("High ratio of articles without content")
        
        if quality_assessment["source_diversity"] < 2:
            quality_assessment["potential_issues"].append("Low source diversity")
        
        # 全体的な品質判定
        issue_count = len(quality_assessment["potential_issues"])
        if issue_count == 0:
            quality_assessment["overall_quality"] = "excellent"
        elif issue_count <= 1:
            quality_assessment["overall_quality"] = "good"
        elif issue_count <= 2:
            quality_assessment["overall_quality"] = "fair"
        else:
            quality_assessment["overall_quality"] = "poor"
        
        return quality_assessment
    
    def _analyze_trends(self, articles: List[Dict]) -> Dict[str, Any]:
        """トレンド分析"""
        if not articles:
            return {}
        
        # キーワード分析
        all_titles = " ".join([article.get("title", "").lower() for article in articles])
        common_words = self._extract_common_keywords(all_titles)
        
        # ソース別トレンド
        source_trends = {}
        for article in articles:
            source = article.get("source", "unknown")
            if source not in source_trends:
                source_trends[source] = []
            source_trends[source].append({
                "title": article.get("title", ""),
                "score": article.get("score", 0)
            })
        
        return {
            "trending_keywords": common_words,
            "source_trends": source_trends,
            "total_unique_sources": len(source_trends),
            "most_active_source": max(source_trends.keys(), key=lambda x: len(source_trends[x])) if source_trends else None
        }
    
    def _extract_common_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """共通キーワード抽出"""
        import re
        from collections import Counter
        
        # 基本的なキーワード抽出（実際のプロダクションではより高度なNLP処理を使用）
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # ストップワードを除外
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "her", "was", "one", "our", 
            "had", "what", "said", "each", "which", "their", "time", "will", "way", "about", "many", 
            "then", "them", "these", "how", "its", "who", "oil", "sit", "now", "find", "long", "down", 
            "day", "did", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two", 
            "may", "say", "she", "use", "your", "work", "life", "only", "can", "also", "back", "other", 
            "after", "first", "well", "year", "work", "such", "make", "even", "here", "good", "this", 
            "that", "with", "have", "from", "they", "know", "want", "been", "good", "much", "some", 
            "time", "very", "when", "come", "may", "say"
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # 頻出単語をカウント
        word_counts = Counter(filtered_words)
        
        return [word for word, count in word_counts.most_common(top_n)]
    
    def _generate_recommendations(self, orchestration_result, articles: List[Dict]) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        if not orchestration_result:
            recommendations.append("No orchestration data available for analysis")
            return recommendations
        
        # エラー率の評価
        total_articles = orchestration_result.total_articles_collected
        error_count = len(orchestration_result.errors)
        warning_count = len(orchestration_result.warnings)
        
        if total_articles == 0:
            recommendations.append("No articles were collected. Check source configurations and API credentials.")
        elif error_count > total_articles * 0.2:
            recommendations.append("High error rate detected. Review error logs and improve error handling.")
        
        # 検証率の評価
        verification_rate = (orchestration_result.articles_verified / max(total_articles, 1)) * 100
        if verification_rate < 50:
            recommendations.append("Low verification rate. Consider adjusting fact-checking criteria or improving article quality filters.")
        
        # 処理時間の評価
        if orchestration_result.processing_time > 600:  # 10分
            recommendations.append("Processing time is high. Consider implementing parallel processing or caching.")
        
        # ソースの多様性評価
        enabled_sources = len([s for s in orchestration_result.articles_by_source.keys() if orchestration_result.articles_by_source[s] > 0])
        if enabled_sources < 2:
            recommendations.append("Low source diversity. Enable more news sources for comprehensive coverage.")
        
        # パフォーマンス最適化
        if orchestration_result.processing_time / max(total_articles, 1) > 30:  # 記事当たり30秒以上
            recommendations.append("Consider optimizing article processing pipeline for better performance.")
        
        # 要約成功率
        summarization_rate = (orchestration_result.articles_summarized / max(orchestration_result.articles_verified, 1)) * 100
        if summarization_rate < 80:
            recommendations.append("Low summarization success rate. Check Claude CLI configuration and timeout settings.")
        
        if not recommendations:
            recommendations.append("System performance is optimal. Continue monitoring for any degradation.")
        
        return recommendations
    
    def _serialize_orchestration_result(self, orchestration_result) -> Dict[str, Any]:
        """OrchestrationResultのシリアライズ"""
        if not orchestration_result:
            return {}
        
        try:
            # dataclassの場合はasdict()を使用
            if hasattr(orchestration_result, '__dict__'):
                return asdict(orchestration_result)
            else:
                # 通常のオブジェクトの場合は手動変換
                return {
                    "total_articles_collected": getattr(orchestration_result, 'total_articles_collected', 0),
                    "articles_by_source": getattr(orchestration_result, 'articles_by_source', {}),
                    "articles_verified": getattr(orchestration_result, 'articles_verified', 0),
                    "articles_summarized": getattr(orchestration_result, 'articles_summarized', 0),
                    "articles_notified": getattr(orchestration_result, 'articles_notified', 0),
                    "processing_time": getattr(orchestration_result, 'processing_time', 0),
                    "errors": getattr(orchestration_result, 'errors', []),
                    "warnings": getattr(orchestration_result, 'warnings', [])
                }
        except Exception as e:
            self.logger.warning(f"Failed to serialize orchestration result: {e}")
            return {"serialization_error": str(e)}
    
    def get_historical_reports(self, days: int = 7) -> List[str]:
        """
        過去のレポートファイル一覧を取得
        
        Args:
            days: 取得する過去の日数
        
        Returns:
            List[str]: レポートファイルパスのリスト
        """
        try:
            reports = []
            current_date = datetime.now()
            
            for i in range(days):
                date = current_date - timedelta(days=i)
                date_str = date.strftime("%Y%m%d")
                report_filename = f"unified_ai_news_report_{date_str}.json"
                report_path = os.path.join(self.output_dir, report_filename)
                
                if os.path.exists(report_path):
                    reports.append(report_path)
            
            return reports
            
        except Exception as e:
            self.logger.error(f"Failed to get historical reports: {e}")
            return []
    
    def generate_summary_report(self, days: int = 7) -> str:
        """
        過去数日のサマリーレポートを生成
        
        Args:
            days: サマリー対象の日数
        
        Returns:
            str: サマリーレポートファイルのパス
        """
        try:
            historical_reports = self.get_historical_reports(days)
            
            if not historical_reports:
                self.logger.warning("No historical reports found for summary generation")
                return ""
            
            # 各レポートからデータを読み込み
            summary_data = {
                "period": f"{days} days",
                "reports_analyzed": len(historical_reports),
                "total_articles": 0,
                "total_verified": 0,
                "total_notified": 0,
                "avg_processing_time": 0,
                "source_performance": {},
                "daily_summaries": []
            }
            
            processing_times = []
            
            for report_path in historical_reports:
                try:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)
                    
                    summary = report_data.get("summary", {})
                    summary_data["total_articles"] += summary.get("total_articles_collected", 0)
                    summary_data["total_verified"] += summary.get("articles_verified", 0)
                    summary_data["total_notified"] += summary.get("articles_notified", 0)
                    
                    proc_time = summary.get("processing_time_seconds", 0)
                    if proc_time > 0:
                        processing_times.append(proc_time)
                    
                    summary_data["daily_summaries"].append({
                        "date": os.path.basename(report_path).split("_")[-1].replace(".json", ""),
                        "articles": summary.get("total_articles_collected", 0),
                        "verified": summary.get("articles_verified", 0),
                        "success_rate": summary.get("success_rate", 0)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process report {report_path}: {e}")
                    continue
            
            # 平均処理時間
            if processing_times:
                summary_data["avg_processing_time"] = round(statistics.mean(processing_times), 2)
            
            # サマリーレポート保存
            timestamp = datetime.now()
            summary_filename = f"summary_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            summary_path = os.path.join(self.output_dir, summary_filename)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Summary report generated: {summary_path}")
            return summary_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {e}")
            raise


def main():
    """テスト用のメイン関数"""
    # サンプルデータでテスト
    from dataclasses import dataclass
    
    @dataclass
    class SampleOrchestrationResult:
        total_articles_collected: int
        articles_by_source: Dict[str, int]
        articles_verified: int
        articles_summarized: int
        articles_notified: int
        processing_time: float
        errors: List[str]
        warnings: List[str]
    
    sample_result = SampleOrchestrationResult(
        total_articles_collected=15,
        articles_by_source={"hackernews": 5, "reddit": 5, "github": 5},
        articles_verified=12,
        articles_summarized=10,
        articles_notified=11,
        processing_time=45.2,
        errors=["One minor error"],
        warnings=["One warning"]
    )
    
    sample_articles = [
        {
            "source": "hackernews",
            "title": "Revolutionary AI Model Breaks Performance Records",
            "url": "https://example.com/ai-model",
            "score": 150,
            "content": "A new AI model has achieved...",
            "time": datetime.now().isoformat()
        },
        {
            "source": "reddit",
            "title": "Discussion: New AI Developments",
            "url": "https://reddit.com/r/MachineLearning/post",
            "score": 85,
            "content": "Community discussion about...",
            "time": datetime.now().isoformat()
        }
    ]
    
    # レポート生成テスト
    generator = UnifiedReportGenerator()
    
    test_data = {
        "orchestration_result": sample_result,
        "articles": sample_articles,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        report_path = generator.generate_unified_report(test_data)
        print(f"Test report generated: {report_path}")
        
        # レポート内容を表示
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        print("\n=== Report Summary ===")
        summary = report_data.get("summary", {})
        for key, value in summary.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    main()
