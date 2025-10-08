"""異常検知・アラート管理モジュール"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from collections import deque

from config import settings
from src.notification.slack_notifier import SlackNotifier

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """実行結果データ"""
    timestamp: datetime
    success: bool
    articles_found: int
    articles_verified: int
    processing_time_seconds: float
    error_message: Optional[str] = None


@dataclass
class Alert:
    """アラート情報"""
    type: str  # "consecutive_failures", "low_articles", "performance_degradation"
    severity: str  # "warning", "critical"
    message: str
    details: Dict
    timestamp: datetime


class AnomalyDetector:
    """異常検知・アラート管理クラス"""
    
    # ファイルパス
    EXECUTION_HISTORY_FILE = "execution_history.json"
    ALERT_HISTORY_FILE = "alert_history.json"
    
    # 閾値設定
    CONSECUTIVE_FAILURE_THRESHOLD = 3  # 連続失敗回数
    MIN_ARTICLES_WARNING = 2  # 記事数警告閾値
    MIN_ARTICLES_CRITICAL = 0  # 記事数異常閾値
    PERFORMANCE_WARNING_FACTOR = 2.0  # 処理時間警告倍率
    PERFORMANCE_CRITICAL_FACTOR = 3.0  # 処理時間異常倍率
    
    def __init__(self):
        self.slack_notifier = SlackNotifier()
        self.execution_history = deque(maxlen=100)  # 最新100件を保持
        self.alert_history = []
        self.baseline_performance = None
        
        self._load_history()
        self._calculate_baseline()
    
    def record_execution(self, result: ExecutionResult):
        """実行結果を記録"""
        self.execution_history.append({
            'timestamp': result.timestamp.isoformat(),
            'success': result.success,
            'articles_found': result.articles_found,
            'articles_verified': result.articles_verified,
            'processing_time_seconds': result.processing_time_seconds,
            'error_message': result.error_message
        })
        
        self._save_history()
        
        # 異常検知実行
        alerts = self._detect_anomalies(result)
        
        # アラート送信
        for alert in alerts:
            self._send_alert(alert)
    
    def _detect_anomalies(self, latest_result: ExecutionResult) -> List[Alert]:
        """異常を検知"""
        alerts = []
        
        # 1. 連続実行失敗チェック
        failure_alert = self._check_consecutive_failures()
        if failure_alert:
            alerts.append(failure_alert)
        
        # 2. 記事数異常チェック
        if latest_result.success:
            article_alert = self._check_article_count(latest_result)
            if article_alert:
                alerts.append(article_alert)
        
        # 3. パフォーマンス劣化チェック
        if latest_result.success and self.baseline_performance:
            performance_alert = self._check_performance(latest_result)
            if performance_alert:
                alerts.append(performance_alert)
        
        return alerts
    
    def _check_consecutive_failures(self) -> Optional[Alert]:
        """連続実行失敗をチェック"""
        if len(self.execution_history) < self.CONSECUTIVE_FAILURE_THRESHOLD:
            return None
        
        # 最新のN件をチェック
        recent_executions = list(self.execution_history)[-self.CONSECUTIVE_FAILURE_THRESHOLD:]
        all_failed = all(not exec_data['success'] for exec_data in recent_executions)
        
        if all_failed:
            error_messages = [
                exec_data['error_message'] 
                for exec_data in recent_executions 
                if exec_data['error_message']
            ]
            
            return Alert(
                type="consecutive_failures",
                severity="critical",
                message=f"🚨 {self.CONSECUTIVE_FAILURE_THRESHOLD}回連続で実行に失敗しています",
                details={
                    'failure_count': self.CONSECUTIVE_FAILURE_THRESHOLD,
                    'error_messages': error_messages
                },
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_article_count(self, result: ExecutionResult) -> Optional[Alert]:
        """記事数異常をチェック"""
        if result.articles_verified <= self.MIN_ARTICLES_CRITICAL:
            return Alert(
                type="low_articles",
                severity="critical",
                message=f"🚨 検証済み記事が{result.articles_verified}件しかありません",
                details={
                    'articles_found': result.articles_found,
                    'articles_verified': result.articles_verified,
                    'expected_minimum': settings.MAX_ARTICLES_PER_DAY
                },
                timestamp=datetime.now()
            )
        elif result.articles_verified <= self.MIN_ARTICLES_WARNING:
            return Alert(
                type="low_articles",
                severity="warning",
                message=f"⚠️ 検証済み記事が少なくなっています（{result.articles_verified}件）",
                details={
                    'articles_found': result.articles_found,
                    'articles_verified': result.articles_verified,
                    'expected': settings.MAX_ARTICLES_PER_DAY
                },
                timestamp=datetime.now()
            )
        
        return None
    
    def _check_performance(self, result: ExecutionResult) -> Optional[Alert]:
        """パフォーマンス劣化をチェック"""
        if not self.baseline_performance:
            return None
        
        baseline_time = self.baseline_performance['avg_processing_time']
        current_time = result.processing_time_seconds
        
        if current_time > baseline_time * self.PERFORMANCE_CRITICAL_FACTOR:
            return Alert(
                type="performance_degradation",
                severity="critical",
                message=f"🚨 処理時間が異常に長くなっています（{current_time:.1f}秒）",
                details={
                    'current_time': current_time,
                    'baseline_time': baseline_time,
                    'factor': current_time / baseline_time
                },
                timestamp=datetime.now()
            )
        elif current_time > baseline_time * self.PERFORMANCE_WARNING_FACTOR:
            return Alert(
                type="performance_degradation",
                severity="warning",
                message=f"⚠️ 処理時間が増加しています（{current_time:.1f}秒）",
                details={
                    'current_time': current_time,
                    'baseline_time': baseline_time,
                    'factor': current_time / baseline_time
                },
                timestamp=datetime.now()
            )
        
        return None
    
    def _send_alert(self, alert: Alert):
        """アラートを送信"""
        # 重複アラート防止（同じタイプのアラートは1時間に1回まで）
        if self._is_duplicate_alert(alert):
            logger.info(f"重複アラートのため送信をスキップ: {alert.type}")
            return
        
        # アラート履歴に追加
        self.alert_history.append({
            'type': alert.type,
            'severity': alert.severity,
            'message': alert.message,
            'details': alert.details,
            'timestamp': alert.timestamp.isoformat()
        })
        self._save_alert_history()
        
        # Slack簡易テキスト通知に移行
        title_emoji = "🔴" if alert.severity == "critical" else "⚠️"
        lines = [
            f"{title_emoji} AI News Feeder アラート",
            f"種別: {self._get_alert_type_name(alert.type)}",
            f"重要度: {alert.severity.upper()}",
            alert.message,
        ]
        # 詳細追記
        if alert.type == "consecutive_failures" and alert.details.get('error_messages'):
            lines.append(f"最新エラー: {alert.details['error_messages'][-1][:200]}")
        elif alert.type == "low_articles":
            lines.append(
                f"記事数: 検証済み {alert.details['articles_verified']} / 発見 {alert.details['articles_found']}"
            )
        elif alert.type == "performance_degradation":
            lines.append(
                f"処理時間: {alert.details['current_time']:.1f}s (通常の{alert.details['factor']:.1f}倍)"
            )
        text = "\n".join(lines)
        ok = self.slack_notifier.send_notification(text)
        if ok:
            logger.info(f"アラート送信成功: {alert.type}")
        else:
            logger.error("アラート送信失敗")
    
    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """重複アラートかチェック（1時間以内の同じタイプ）"""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        for past_alert in reversed(self.alert_history):
            alert_time = datetime.fromisoformat(past_alert['timestamp'])
            if alert_time < one_hour_ago:
                break
            
            if past_alert['type'] == alert.type and past_alert['severity'] == alert.severity:
                return True
        
        return False
    
    def _get_alert_type_name(self, alert_type: str) -> str:
        """アラートタイプの日本語名を取得"""
        names = {
            'consecutive_failures': '連続実行失敗',
            'low_articles': '記事数不足',
            'performance_degradation': 'パフォーマンス劣化'
        }
        return names.get(alert_type, alert_type)
    
    def _calculate_baseline(self):
        """ベースライン性能を計算"""
        if len(self.execution_history) < 10:
            return
        
        # 成功した実行のみを対象
        successful_executions = [
            exec_data for exec_data in self.execution_history
            if exec_data['success']
        ]
        
        if len(successful_executions) < 5:
            return
        
        # 最新20件の平均を計算
        recent_successful = successful_executions[-20:]
        avg_time = sum(exec_data['processing_time_seconds'] for exec_data in recent_successful) / len(recent_successful)
        avg_articles = sum(exec_data['articles_verified'] for exec_data in recent_successful) / len(recent_successful)
        
        self.baseline_performance = {
            'avg_processing_time': avg_time,
            'avg_articles_verified': avg_articles,
            'sample_size': len(recent_successful)
        }
        
        logger.info(f"ベースライン計算完了: 平均処理時間={avg_time:.1f}秒, 平均記事数={avg_articles:.1f}")
    
    def _save_history(self):
        """実行履歴を保存"""
        try:
            with open(self.EXECUTION_HISTORY_FILE, 'w') as f:
                json.dump(list(self.execution_history), f, indent=2)
        except Exception as e:
            logger.error(f"実行履歴保存エラー: {e}")
    
    def _save_alert_history(self):
        """アラート履歴を保存"""
        try:
            # 最新100件のみ保持
            self.alert_history = self.alert_history[-100:]
            
            with open(self.ALERT_HISTORY_FILE, 'w') as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            logger.error(f"アラート履歴保存エラー: {e}")
    
    def _load_history(self):
        """履歴を読み込み"""
        # 実行履歴
        if os.path.exists(self.EXECUTION_HISTORY_FILE):
            try:
                with open(self.EXECUTION_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.execution_history = deque(data, maxlen=100)
            except Exception as e:
                logger.error(f"実行履歴読み込みエラー: {e}")
        
        # アラート履歴
        if os.path.exists(self.ALERT_HISTORY_FILE):
            try:
                with open(self.ALERT_HISTORY_FILE, 'r') as f:
                    self.alert_history = json.load(f)
            except Exception as e:
                logger.error(f"アラート履歴読み込みエラー: {e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """最近のアラートを取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['timestamp'])
            if alert_time >= cutoff_time:
                recent.append(alert)
        
        return recent
    
    def get_execution_stats(self) -> Dict:
        """実行統計を取得"""
        if not self.execution_history:
            return {}
        
        total = len(self.execution_history)
        successful = sum(1 for exec_data in self.execution_history if exec_data['success'])
        
        # 24時間以内の統計
        day_ago = datetime.now() - timedelta(hours=24)
        recent_executions = [
            exec_data for exec_data in self.execution_history
            if datetime.fromisoformat(exec_data['timestamp']) >= day_ago
        ]
        
        recent_total = len(recent_executions)
        recent_successful = sum(1 for exec_data in recent_executions if exec_data['success'])
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'recent_24h': {
                'total': recent_total,
                'successful': recent_successful,
                'success_rate': (recent_successful / recent_total * 100) if recent_total > 0 else 0
            },
            'baseline_performance': self.baseline_performance
        }
