#!/usr/bin/env python3
"""ヘルスチェック実行・監視スクリプト"""
import sys
import os
import argparse
import time
from datetime import datetime, timedelta
import schedule
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.health_checker import HealthChecker
from src.notification.slack_notifier import SlackNotifier
import logging

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HealthMonitor:
    """ヘルス監視管理クラス"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.slack_notifier = SlackNotifier()
        self.last_notification_time = None
        self.notification_interval = timedelta(hours=1)  # 通知間隔
        
    def run_check(self, notify=True):
        """ヘルスチェックを実行"""
        logger.info("ヘルスチェック実行中...")
        
        # ヘルスチェック実行
        health = self.health_checker.check_all()
        
        # コンソール出力
        self._print_health_report(health)
        
        # 異常時の通知
        if notify and health.status != "healthy":
            self._notify_if_needed(health)
        
        return health
    
    def _print_health_report(self, health):
        """ヘルスレポートをコンソールに出力"""
        print("\n" + "="*60)
        print("🏥 システムヘルスチェックレポート")
        print("="*60)
        
        # ステータス絵文字
        status_emoji = {
            'healthy': '🟢',
            'degraded': '🟡', 
            'unhealthy': '🔴'
        }.get(health.status, '⚪')
        
        print(f"\n{status_emoji} 全体ステータス: {health.status.upper()}")
        print(f"チェック項目: {health.checks_passed}/{health.checks_total} 成功")
        print(f"実行時刻: {health.timestamp.strftime('%Y/%m/%d %H:%M:%S')}")
        
        if health.uptime_hours:
            print(f"稼働時間: {health.uptime_hours:.1f}時間")
        
        if health.last_successful_run:
            print(f"最終成功実行: {health.last_successful_run.strftime('%Y/%m/%d %H:%M')}")
        
        print("\n📊 コンポーネント状態:")
        print("-" * 60)
        
        for component in health.components:
            comp_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌'
            }.get(component.status, '❓')
            
            print(f"{comp_emoji} {component.name:<20} {component.message}")
            
            if component.response_time_ms:
                print(f"   応答時間: {component.response_time_ms:.0f}ms")
        
        print("="*60 + "\n")
    
    def _notify_if_needed(self, health):
        """必要に応じてSlack通知"""
        # 通知間隔のチェック
        now = datetime.now()
        if self.last_notification_time:
            if now - self.last_notification_time < self.notification_interval:
                logger.info("通知間隔内のため、Slack通知をスキップ")
                return
        
        # 簡易テキスト通知に統一
        issues = [f"• {c.name}: {c.message}" for c in health.components if c.status != 'healthy']
        status_emoji = {
            'unhealthy': '🔴',
            'degraded': '🟡'
        }.get(health.status, '⚪')
        text = (
            f"{status_emoji} ヘルスチェック異常検知\n"
            f"ステータス: {health.status.upper()}  成功: {health.checks_passed}/{health.checks_total}\n"
            f"時刻: {health.timestamp.strftime('%Y/%m/%d %H:%M')}\n"
            f"問題コンポーネント:\n" + ("\n".join(issues) if issues else "なし")
        )
        if self.slack_notifier.send_notification(text):
            logger.info("Slack通知送信成功")
            self.last_notification_time = now
        else:
            logger.error("Slack通知送信失敗")
    
    def run_continuous(self, interval_minutes=30):
        """定期的なヘルスチェックを実行"""
        logger.info(f"{interval_minutes}分間隔でヘルスチェックを開始します")
        
        # 初回実行
        self.run_check()
        
        # スケジュール設定
        schedule.every(interval_minutes).minutes.do(self.run_check)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("ヘルスチェック監視を停止します")
    
    def show_history(self, limit=20):
        """ヘルスチェック履歴を表示"""
        if not os.path.exists(self.health_checker.HISTORY_FILE):
            print("履歴ファイルが見つかりません")
            return
        
        try:
            with open(self.health_checker.HISTORY_FILE, 'r') as f:
                history = json.load(f)
            
            print("\n📈 ヘルスチェック履歴")
            print("="*70)
            print(f"{'時刻':<20} {'ステータス':<12} {'成功/合計':<10}")
            print("-"*70)
            
            # 最新のものから表示
            for item in history[-limit:][::-1]:
                timestamp = datetime.fromisoformat(item['timestamp'])
                status = item['status']
                checks = f"{item['checks_passed']}/{item['checks_total']}"
                
                status_emoji = {
                    'healthy': '🟢',
                    'degraded': '🟡',
                    'unhealthy': '🔴'
                }.get(status, '⚪')
                
                print(f"{timestamp.strftime('%Y/%m/%d %H:%M')} {status_emoji} {status:<10} {checks}")
            
        except Exception as e:
            print(f"履歴読み込みエラー: {e}")
    
    def get_statistics(self):
        """統計情報を表示"""
        if not os.path.exists(self.health_checker.HISTORY_FILE):
            print("履歴ファイルが見つかりません")
            return
        
        try:
            with open(self.health_checker.HISTORY_FILE, 'r') as f:
                history = json.load(f)
            
            if not history:
                print("履歴データがありません")
                return
            
            # 統計計算
            total = len(history)
            healthy = sum(1 for h in history if h['status'] == 'healthy')
            degraded = sum(1 for h in history if h['status'] == 'degraded')
            unhealthy = sum(1 for h in history if h['status'] == 'unhealthy')
            
            # 成功率計算
            total_checks = sum(h['checks_total'] for h in history)
            passed_checks = sum(h['checks_passed'] for h in history)
            success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            print("\n📊 ヘルスチェック統計")
            print("="*50)
            print(f"総チェック回数: {total}")
            print(f"期間: {history[0]['timestamp'][:10]} 〜 {history[-1]['timestamp'][:10]}")
            print("\nステータス別:")
            print(f"  🟢 Healthy:   {healthy:4d} ({healthy/total*100:5.1f}%)")
            print(f"  🟡 Degraded:  {degraded:4d} ({degraded/total*100:5.1f}%)")
            print(f"  🔴 Unhealthy: {unhealthy:4d} ({unhealthy/total*100:5.1f}%)")
            print(f"\n個別チェック成功率: {success_rate:.1f}%")
            
        except Exception as e:
            print(f"統計計算エラー: {e}")


def main():
    parser = argparse.ArgumentParser(description='システムヘルスチェック監視ツール')
    
    parser.add_argument('--check', action='store_true',
                       help='ヘルスチェックを1回実行')
    parser.add_argument('--monitor', action='store_true',
                       help='継続的な監視を開始')
    parser.add_argument('--interval', type=int, default=30,
                       help='監視間隔（分）、デフォルト: 30')
    parser.add_argument('--history', action='store_true',
                       help='ヘルスチェック履歴を表示')
    parser.add_argument('--stats', action='store_true',
                       help='統計情報を表示')
    parser.add_argument('--no-notify', action='store_true',
                       help='Slack通知を無効化')
    
    args = parser.parse_args()
    
    monitor = HealthMonitor()
    
    if args.check:
        # 単発実行
        monitor.run_check(notify=not args.no_notify)
        
    elif args.monitor:
        # 継続監視
        monitor.run_continuous(interval_minutes=args.interval)
        
    elif args.history:
        # 履歴表示
        monitor.show_history()
        
    elif args.stats:
        # 統計表示
        monitor.get_statistics()
        
    else:
        # デフォルト: ステータスサマリー表示
        summary = monitor.health_checker.get_status_summary()
        print(summary)


if __name__ == "__main__":
    main()
