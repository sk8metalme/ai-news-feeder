"""ニュース処理のメインロジック"""
import logging
from typing import List, Dict
from datetime import datetime

from src.api.hacker_news import HackerNewsAPI
from src.verification.fact_checker import FactChecker
from src.notification.slack_notifier import SlackNotifier
from config import settings
from src.utils.health_checker import HealthChecker
from src.utils.anomaly_detector import AnomalyDetector, ExecutionResult

logger = logging.getLogger(__name__)


class NewsProcessor:
    """ニュースの収集、検証、通知を統括するクラス"""
    
    def __init__(self):
        self.hn_api = HackerNewsAPI()
        self.fact_checker = FactChecker(enable_summarization=settings.ENABLE_SUMMARIZATION)
        self.slack_notifier = SlackNotifier()
        self.health_checker = HealthChecker()
        self.anomaly_detector = AnomalyDetector()
    
    def process_daily_news(self) -> bool:
        """日次のニュース処理を実行"""
        start_time = datetime.now()
        articles_found = 0
        articles_verified = 0
        error_message = None
        
        try:
            logger.info("AI News Feeder - 日次処理を開始します")
            
            # 1. Hacker NewsからAI関連記事を取得
            logger.info("Hacker NewsからAI関連記事を検索中...")
            stories = self.hn_api.get_ai_stories(
                max_stories=200,
                hours=settings.CHECK_INTERVAL_HOURS,
            )
            
            if not stories:
                logger.warning("AI関連記事が見つかりませんでした")
                error_message = "AI関連記事が見つかりませんでした"
                return False
            
            articles_found = len(stories)
            logger.info(f"{articles_found}件のAI関連記事を発見しました")
            
            # 2. 各記事の信憑性を検証
            verification_results = []
            
            for story in stories:
                logger.info(f"検証中: {story.get('title')}")
                
                # ファクトチェック実行
                result = self.fact_checker.verify_article(
                    story.get('title', ''), story.get('url', '')
                )
                verification_results.append(result)
                logger.info(f"検証: {story.get('title')} → {result.get('verification_status')}")
                
                # 必要な記事数に達したら終了
                if len(verification_results) >= settings.MAX_ARTICLES_PER_DAY:
                    break
            
            # 3. 検証結果をSlackに投稿（デイリーサマリー）
            articles_verified = sum(1 for r in verification_results if r.get('verification_status') == 'verified')
            if verification_results:
                logger.info(f"{articles_verified}件の検証結果をSlackに送信中...")
                success = self.slack_notifier.send_daily_summary(verification_results)
                if success:
                    logger.info("Slackへの送信が完了しました")
                    self._save_report(verification_results)
                    return True
                else:
                    logger.error("Slackへの送信に失敗しました")
                    error_message = "Slackへの送信に失敗しました"
                    return False
            else:
                logger.warning("検証結果が0件でした")
                error_message = "検証結果が0件でした"
                self.slack_notifier.send_notification("本日は検証対象の記事がありませんでした")
                return False
                
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
            error_message = str(e)
            self.slack_notifier.send_error_notification(str(e))
            return False
        
        finally:
            # 実行結果を記録
            processing_time = (datetime.now() - start_time).total_seconds()
            execution_result = ExecutionResult(
                timestamp=start_time,
                success=error_message is None,
                articles_found=articles_found,
                articles_verified=articles_verified,
                processing_time_seconds=processing_time,
                error_message=error_message
            )
            
            self.anomaly_detector.record_execution(execution_result)
            logger.info(f"処理時間: {processing_time:.1f}秒")
    
    def _save_report(self, results: List[Dict]):
        """レポートをローカルに保存（オプション）"""
        try:
            import json
            import os
            
            # reportsディレクトリを作成
            os.makedirs('reports', exist_ok=True)
            
            # ファイル名に日付を含める
            filename = f"reports/ai_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # JSON形式で保存
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': results,
                    'total_count': len(results)
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"レポートを保存しました: {filename}")
            
        except Exception as e:
            logger.error(f"レポート保存エラー: {e}")


def run_daily_process():
    """日次処理のエントリーポイント"""
    # ロガー設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ai_news_feeder.log'),
            logging.StreamHandler()
        ]
    )
    
    # 設定の簡易チェック（任意）
    # Slack Webhook が未設定でも他機能は動作するため、ここでは必須チェックを行わない
    
    # 処理実行
    processor = NewsProcessor()
    return processor.process_daily_news()


if __name__ == "__main__":
    run_daily_process()
