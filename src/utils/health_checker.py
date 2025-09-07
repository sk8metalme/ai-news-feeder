"""ヘルスチェック機能モジュール"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass, asdict
import json
import os

from src.utils.config import Config
from src.api.hackernews_api import HackerNewsAPI
from src.api.factcheck_api import FactCheckAPI
from src.utils.slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


@dataclass
class ComponentHealth:
    """コンポーネントの健康状態"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


@dataclass
class SystemHealth:
    """システム全体の健康状態"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    components: List[ComponentHealth]
    checks_passed: int
    checks_total: int
    uptime_hours: Optional[float] = None
    last_successful_run: Optional[datetime] = None


class HealthChecker:
    """システムヘルスチェック管理クラス"""
    
    # ヘルスチェック結果ファイル
    HEALTH_FILE = "health_status.json"
    HISTORY_FILE = "health_history.json"
    
    def __init__(self):
        self.start_time = datetime.now()
        self.hn_api = HackerNewsAPI()
        self.fc_api = FactCheckAPI()
        self.slack_notifier = SlackNotifier()
        
        # ヘルスチェック履歴
        self.history = []
        self._load_history()
    
    def check_all(self) -> SystemHealth:
        """全コンポーネントのヘルスチェックを実行"""
        logger.info("ヘルスチェック開始")
        
        components = []
        
        # 各コンポーネントをチェック
        components.append(self._check_hackernews_api())
        components.append(self._check_devto_api())
        components.append(self._check_medium_rss())
        components.append(self._check_slack_webhook())
        components.append(self._check_file_system())
        components.append(self._check_config())
        
        # 全体のステータスを判定
        unhealthy_count = sum(1 for c in components if c.status == "unhealthy")
        degraded_count = sum(1 for c in components if c.status == "degraded")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # アップタイムを計算
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # 最後の成功実行時刻を取得
        last_successful_run = self._get_last_successful_run()
        
        health = SystemHealth(
            status=overall_status,
            timestamp=datetime.now(),
            components=components,
            checks_passed=len(components) - unhealthy_count,
            checks_total=len(components),
            uptime_hours=uptime_hours,
            last_successful_run=last_successful_run
        )
        
        # 結果を保存
        self._save_health_status(health)
        self._add_to_history(health)
        
        logger.info(f"ヘルスチェック完了: {overall_status}")
        
        return health
    
    def _check_hackernews_api(self) -> ComponentHealth:
        """Hacker News APIの接続チェック"""
        name = "Hacker News API"
        start_time = time.time()
        
        try:
            # トップストーリーを1件だけ取得してテスト
            story_ids = self.hn_api.get_top_stories(limit=1)
            
            if story_ids:
                response_time = (time.time() - start_time) * 1000
                return ComponentHealth(
                    name=name,
                    status="healthy",
                    message="API接続正常",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="unhealthy",
                    message="APIレスポンスが空",
                    last_check=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Hacker News APIチェックエラー: {e}")
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=f"エラー: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_devto_api(self) -> ComponentHealth:
        """dev.to APIの接続チェック"""
        name = "dev.to API"
        start_time = time.time()
        
        try:
            url = f"{self.fc_api.dev_to_base}/articles?page=1&per_page=1"
            response = requests.get(url, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    name=name,
                    status="healthy",
                    message="API接続正常",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="degraded",
                    message=f"HTTPステータス: {response.status_code}",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
                
        except Exception as e:
            logger.error(f"dev.to APIチェックエラー: {e}")
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=f"エラー: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_medium_rss(self) -> ComponentHealth:
        """Medium RSSフィードの接続チェック"""
        name = "Medium RSS"
        start_time = time.time()
        
        try:
            # AIタグのRSSフィードをチェック
            url = f"{self.fc_api.medium_rss_base}artificial-intelligence"
            response = requests.get(url, timeout=10)
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    name=name,
                    status="healthy",
                    message="RSSフィード正常",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="degraded",
                    message=f"HTTPステータス: {response.status_code}",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
                
        except Exception as e:
            logger.error(f"Medium RSSチェックエラー: {e}")
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=f"エラー: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_slack_webhook(self) -> ComponentHealth:
        """Slack Webhookの検証（実際には送信しない）"""
        name = "Slack Webhook"
        
        if not Config.SLACK_WEBHOOK_URL:
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message="Webhook URLが設定されていません",
                last_check=datetime.now()
            )
        
        # URL形式の基本的な検証
        if Config.SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com/services/"):
            return ComponentHealth(
                name=name,
                status="healthy",
                message="Webhook URL形式正常",
                last_check=datetime.now()
            )
        else:
            return ComponentHealth(
                name=name,
                status="degraded",
                message="Webhook URL形式が異常",
                last_check=datetime.now()
            )
    
    def _check_file_system(self) -> ComponentHealth:
        """ファイルシステムの書き込み権限チェック"""
        name = "File System"
        
        try:
            # reportsディレクトリの存在と書き込み権限をチェック
            os.makedirs('reports', exist_ok=True)
            test_file = 'reports/.health_check_test'
            
            with open(test_file, 'w') as f:
                f.write('test')
            
            os.remove(test_file)
            
            return ComponentHealth(
                name=name,
                status="healthy",
                message="ファイルシステム書き込み可能",
                last_check=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"ファイルシステムチェックエラー: {e}")
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=f"書き込みエラー: {str(e)}",
                last_check=datetime.now()
            )
    
    def _check_config(self) -> ComponentHealth:
        """設定の妥当性チェック"""
        name = "Configuration"
        
        try:
            Config.validate()
            
            # 追加の設定チェック
            warnings = []
            
            if Config.ARTICLES_PER_DAY > 10:
                warnings.append("記事数が多すぎる可能性があります")
            
            if Config.FACTCHECK_CONFIDENCE_THRESHOLD > 0.8:
                warnings.append("信頼度閾値が高すぎる可能性があります")
            
            if warnings:
                return ComponentHealth(
                    name=name,
                    status="degraded",
                    message=f"警告: {', '.join(warnings)}",
                    last_check=datetime.now(),
                    details={"warnings": warnings}
                )
            else:
                return ComponentHealth(
                    name=name,
                    status="healthy",
                    message="設定正常",
                    last_check=datetime.now()
                )
                
        except Exception as e:
            return ComponentHealth(
                name=name,
                status="unhealthy",
                message=f"設定エラー: {str(e)}",
                last_check=datetime.now()
            )
    
    def _save_health_status(self, health: SystemHealth):
        """ヘルスステータスをファイルに保存"""
        try:
            data = {
                'status': health.status,
                'timestamp': health.timestamp.isoformat(),
                'checks_passed': health.checks_passed,
                'checks_total': health.checks_total,
                'uptime_hours': health.uptime_hours,
                'last_successful_run': health.last_successful_run.isoformat() if health.last_successful_run else None,
                'components': [
                    {
                        'name': c.name,
                        'status': c.status,
                        'message': c.message,
                        'last_check': c.last_check.isoformat(),
                        'response_time_ms': c.response_time_ms,
                        'details': c.details
                    }
                    for c in health.components
                ]
            }
            
            with open(self.HEALTH_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"ヘルスステータス保存エラー: {e}")
    
    def _add_to_history(self, health: SystemHealth):
        """ヘルスチェック履歴に追加"""
        self.history.append({
            'timestamp': health.timestamp.isoformat(),
            'status': health.status,
            'checks_passed': health.checks_passed,
            'checks_total': health.checks_total
        })
        
        # 最新100件のみ保持
        self.history = self.history[-100:]
        
        try:
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"履歴保存エラー: {e}")
    
    def _load_history(self):
        """履歴を読み込み"""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                logger.error(f"履歴読み込みエラー: {e}")
                self.history = []
    
    def _get_last_successful_run(self) -> Optional[datetime]:
        """最後の成功実行時刻を取得"""
        # reportsディレクトリから最新のレポートを探す
        try:
            if os.path.exists('reports'):
                files = [f for f in os.listdir('reports') if f.startswith('ai_news_')]
                if files:
                    # ファイル名から日時を抽出
                    latest = sorted(files)[-1]
                    date_str = latest.replace('ai_news_', '').replace('.json', '')
                    return datetime.strptime(date_str, '%Y%m%d_%H%M%S')
        except Exception as e:
            logger.error(f"最終実行時刻取得エラー: {e}")
        
        return None
    
    def get_status_summary(self) -> str:
        """ステータスサマリーを取得"""
        if os.path.exists(self.HEALTH_FILE):
            try:
                with open(self.HEALTH_FILE, 'r') as f:
                    data = json.load(f)
                
                status = data['status']
                checks = f"{data['checks_passed']}/{data['checks_total']}"
                timestamp = datetime.fromisoformat(data['timestamp'])
                
                # ステータス絵文字
                emoji = {
                    'healthy': '🟢',
                    'degraded': '🟡',
                    'unhealthy': '🔴'
                }.get(status, '⚪')
                
                summary = f"{emoji} システムステータス: {status.upper()}\n"
                summary += f"チェック結果: {checks}\n"
                summary += f"最終チェック: {timestamp.strftime('%Y/%m/%d %H:%M')}\n"
                
                # 問題のあるコンポーネントをリスト
                issues = []
                for component in data['components']:
                    if component['status'] != 'healthy':
                        issues.append(f"- {component['name']}: {component['message']}")
                
                if issues:
                    summary += "\n⚠️ 問題のあるコンポーネント:\n"
                    summary += "\n".join(issues)
                
                return summary
                
            except Exception as e:
                logger.error(f"ステータスサマリー取得エラー: {e}")
                return "ヘルスステータス取得エラー"
        else:
            return "ヘルスチェック未実行"