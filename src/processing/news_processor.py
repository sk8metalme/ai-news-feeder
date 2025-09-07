"""ニュース処理のメインロジック"""
import logging
from typing import List, Dict
from datetime import datetime

from src.api.hackernews_api import HackerNewsAPI
from src.api.factcheck_api import FactCheckAPI
from src.utils.slack_notifier import SlackNotifier
from src.utils.config import Config

logger = logging.getLogger(__name__)


class NewsProcessor:
    """ニュースの収集、検証、通知を統括するクラス"""
    
    def __init__(self):
        self.hn_api = HackerNewsAPI()
        self.factcheck_api = FactCheckAPI()
        self.slack_notifier = SlackNotifier()
    
    def process_daily_news(self) -> bool:
        """日次のニュース処理を実行"""
        try:
            logger.info("AI News Feeder - 日次処理を開始します")
            
            # 1. Hacker NewsからAI関連記事を取得
            logger.info("Hacker NewsからAI関連記事を検索中...")
            stories = self.hn_api.search_ai_stories(hours=24)
            
            if not stories:
                logger.warning("AI関連記事が見つかりませんでした")
                return False
            
            logger.info(f"{len(stories)}件のAI関連記事を発見しました")
            
            # 2. 各記事の信憑性を検証
            verified_articles = []
            
            for story in stories:
                logger.info(f"検証中: {story.get('title')}")
                
                # ファクトチェック実行
                verification = self.factcheck_api.verify_story(story.get('title', ''))
                
                if verification['verified'] and verification.get('confidence_score', 0) >= Config.FACTCHECK_CONFIDENCE_THRESHOLD:
                    article_data = {
                        'title': story.get('title'),
                        'url': story.get('url'),
                        'score': story.get('score', 0),
                        'time': story.get('time'),
                        'verification': verification
                    }
                    verified_articles.append(article_data)
                    logger.info(f"✅ 検証済み: {story.get('title')} (信頼度: {verification.get('confidence_score', 0):.2f})")
                else:
                    logger.info(f"❌ 検証失敗: {story.get('title')} (信頼度: {verification.get('confidence_score', 0):.2f})")
                
                # 必要な記事数に達したら終了
                if len(verified_articles) >= Config.ARTICLES_PER_DAY:
                    break
            
            # 3. 検証済み記事をSlackに投稿
            if verified_articles:
                logger.info(f"{len(verified_articles)}件の検証済み記事をSlackに送信中...")
                success = self.slack_notifier.send_verification_report(verified_articles)
                
                if success:
                    logger.info("Slackへの送信が完了しました")
                    self._save_report(verified_articles)
                    return True
                else:
                    logger.error("Slackへの送信に失敗しました")
                    return False
            else:
                logger.warning("検証済み記事が0件でした")
                self.slack_notifier.send_error_notification(
                    "本日は検証済みのAI関連記事が見つかりませんでした"
                )
                return False
                
        except Exception as e:
            logger.error(f"処理中にエラーが発生しました: {e}")
            self.slack_notifier.send_error_notification(str(e))
            return False
    
    def _save_report(self, articles: List[Dict]):
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
                    'articles': articles,
                    'total_count': len(articles)
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
    
    # 設定の検証
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"設定エラー: {e}")
        return False
    
    # 処理実行
    processor = NewsProcessor()
    return processor.process_daily_news()


if __name__ == "__main__":
    run_daily_process()