#!/usr/bin/env python3
"""実行統計レポート生成スクリプト"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.health_checker import HealthChecker
from src.utils.anomaly_detector import AnomalyDetector
from src.utils.slack_notifier import SlackNotifier
from src.utils.config import Config
import logging

logger = logging.getLogger(__name__)


class StatisticsReporter:
    """統計レポート生成クラス"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.anomaly_detector = AnomalyDetector()
        self.slack_notifier = SlackNotifier()
    
    def generate_daily_report(self):
        """日次レポートを生成"""
        print("\n" + "="*70)
        print("📊 AI News Feeder 日次レポート")
        print("="*70)
        
        # 対象期間
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        print(f"期間: {start_time.strftime('%Y/%m/%d %H:%M')} - {end_time.strftime('%Y/%m/%d %H:%M')}")
        print()
        
        # 実行統計
        self._print_execution_stats(hours=24)
        
        # ヘルスチェック統計
        self._print_health_stats(hours=24)
        
        # アラート統計
        self._print_alert_stats(hours=24)
        
        # パフォーマンス分析
        self._print_performance_analysis(hours=24)
        
        print("="*70 + "\n")
    
    def generate_weekly_report(self):
        """週次レポートを生成"""
        print("\n" + "="*70)
        print("📈 AI News Feeder 週次レポート")
        print("="*70)
        
        # 対象期間
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        print(f"期間: {start_time.strftime('%Y/%m/%d')} - {end_time.strftime('%Y/%m/%d')}")
        print()
        
        # 実行統計
        self._print_execution_stats(hours=168)  # 7日間
        
        # 日別サマリー
        self._print_daily_summary(days=7)
        
        # ヘルスチェック統計
        self._print_health_stats(hours=168)
        
        # アラート統計
        self._print_alert_stats(hours=168)
        
        # トレンド分析
        self._print_trend_analysis(days=7)
        
        print("="*70 + "\n")
    
    def _print_execution_stats(self, hours: int):
        """実行統計を出力"""
        print("📋 実行統計:")
        print("-" * 50)
        
        stats = self.anomaly_detector.get_execution_stats()
        
        if not stats:
            print("データなし")
            return
        
        if hours == 24:
            # 24時間の統計
            recent = stats.get('recent_24h', {})
            print(f"実行回数: {recent.get('total', 0)}")
            print(f"成功回数: {recent.get('successful', 0)}")
            print(f"成功率: {recent.get('success_rate', 0):.1f}%")
        else:
            # 全体統計
            print(f"総実行回数: {stats.get('total_executions', 0)}")
            print(f"成功回数: {stats.get('successful_executions', 0)}")
            print(f"成功率: {stats.get('success_rate', 0):.1f}%")
        
        # ベースライン性能
        baseline = stats.get('baseline_performance')
        if baseline:
            print(f"\nベースライン性能:")
            print(f"  平均処理時間: {baseline['avg_processing_time']:.1f}秒")
            print(f"  平均検証記事数: {baseline['avg_articles_verified']:.1f}件")
        
        print()
    
    def _print_health_stats(self, hours: int):
        """ヘルスチェック統計を出力"""
        print("🏥 ヘルスチェック統計:")
        print("-" * 50)
        
        # 履歴ファイルから統計を計算
        if not os.path.exists(self.health_checker.HISTORY_FILE):
            print("データなし")
            return
        
        try:
            with open(self.health_checker.HISTORY_FILE, 'r') as f:
                history = json.load(f)
            
            # 期間内のデータをフィルタ
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_checks = []
            
            for check in history:
                check_time = datetime.fromisoformat(check['timestamp'])
                if check_time >= cutoff_time:
                    recent_checks.append(check)
            
            if not recent_checks:
                print("期間内のデータなし")
                return
            
            # 統計計算
            total = len(recent_checks)
            healthy = sum(1 for c in recent_checks if c['status'] == 'healthy')
            degraded = sum(1 for c in recent_checks if c['status'] == 'degraded')
            unhealthy = sum(1 for c in recent_checks if c['status'] == 'unhealthy')
            
            print(f"チェック回数: {total}")
            print(f"ステータス分布:")
            print(f"  🟢 Healthy: {healthy} ({healthy/total*100:.1f}%)")
            print(f"  🟡 Degraded: {degraded} ({degraded/total*100:.1f}%)")
            print(f"  🔴 Unhealthy: {unhealthy} ({unhealthy/total*100:.1f}%)")
            
        except Exception as e:
            print(f"エラー: {e}")
        
        print()
    
    def _print_alert_stats(self, hours: int):
        """アラート統計を出力"""
        print("🚨 アラート統計:")
        print("-" * 50)
        
        alerts = self.anomaly_detector.get_recent_alerts(hours=hours)
        
        if not alerts:
            print("アラートなし ✅")
            return
        
        # タイプ別集計
        alert_types = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for alert in alerts:
            alert_types[alert['type']] += 1
            severity_counts[alert['severity']] += 1
        
        print(f"総アラート数: {len(alerts)}")
        print("\n種類別:")
        for alert_type, count in alert_types.items():
            type_name = self.anomaly_detector._get_alert_type_name(alert_type)
            print(f"  {type_name}: {count}件")
        
        print("\n重要度別:")
        for severity, count in severity_counts.items():
            emoji = "🔴" if severity == "critical" else "⚠️"
            print(f"  {emoji} {severity.upper()}: {count}件")
        
        print()
    
    def _print_performance_analysis(self, hours: int):
        """パフォーマンス分析を出力"""
        print("⚡ パフォーマンス分析:")
        print("-" * 50)
        
        # 実行履歴から処理時間を分析
        if not hasattr(self.anomaly_detector, 'execution_history'):
            print("データなし")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        processing_times = []
        article_counts = []
        
        for exec_data in self.anomaly_detector.execution_history:
            exec_time = datetime.fromisoformat(exec_data['timestamp'])
            if exec_time >= cutoff_time and exec_data['success']:
                processing_times.append(exec_data['processing_time_seconds'])
                article_counts.append(exec_data['articles_verified'])
        
        if not processing_times:
            print("成功した実行データなし")
            return
        
        # 統計値計算
        print(f"処理時間:")
        print(f"  最小: {min(processing_times):.1f}秒")
        print(f"  最大: {max(processing_times):.1f}秒")
        print(f"  平均: {statistics.mean(processing_times):.1f}秒")
        if len(processing_times) > 1:
            print(f"  中央値: {statistics.median(processing_times):.1f}秒")
        
        print(f"\n検証記事数:")
        print(f"  最小: {min(article_counts)}件")
        print(f"  最大: {max(article_counts)}件")
        print(f"  平均: {statistics.mean(article_counts):.1f}件")
        
        # 簡易グラフ（処理時間の分布）
        self._print_time_distribution(processing_times)
        
        print()
    
    def _print_time_distribution(self, times):
        """処理時間の分布をテキストグラフで表示"""
        if not times:
            return
        
        print("\n処理時間分布:")
        
        # 10秒単位でビン分け
        bins = defaultdict(int)
        for t in times:
            bin_idx = int(t // 10) * 10
            bins[bin_idx] += 1
        
        # 最大カウントを取得（グラフのスケール用）
        max_count = max(bins.values())
        
        # ソートして表示
        for bin_start in sorted(bins.keys()):
            bin_end = bin_start + 10
            count = bins[bin_start]
            bar_length = int(count / max_count * 30)  # 最大30文字
            bar = "█" * bar_length
            print(f"  {bin_start:3d}-{bin_end:3d}秒: {bar} ({count})")
    
    def _print_daily_summary(self, days: int):
        """日別サマリーを出力"""
        print("📅 日別サマリー:")
        print("-" * 50)
        
        # 日別に集計
        daily_stats = defaultdict(lambda: {
            'executions': 0,
            'successful': 0,
            'articles_verified': 0,
            'processing_time': 0
        })
        
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for exec_data in self.anomaly_detector.execution_history:
            exec_time = datetime.fromisoformat(exec_data['timestamp'])
            if exec_time >= cutoff_time:
                date_key = exec_time.strftime('%Y/%m/%d')
                daily_stats[date_key]['executions'] += 1
                if exec_data['success']:
                    daily_stats[date_key]['successful'] += 1
                    daily_stats[date_key]['articles_verified'] += exec_data['articles_verified']
                    daily_stats[date_key]['processing_time'] += exec_data['processing_time_seconds']
        
        # 日付順にソート
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            success_rate = (stats['successful'] / stats['executions'] * 100) if stats['executions'] > 0 else 0
            avg_time = (stats['processing_time'] / stats['successful']) if stats['successful'] > 0 else 0
            
            print(f"\n{date}:")
            print(f"  実行: {stats['executions']}回 (成功率: {success_rate:.0f}%)")
            print(f"  検証記事: {stats['articles_verified']}件")
            if avg_time > 0:
                print(f"  平均処理時間: {avg_time:.1f}秒")
        
        print()
    
    def _print_trend_analysis(self, days: int):
        """トレンド分析を出力"""
        print("📊 トレンド分析:")
        print("-" * 50)
        
        # 前週との比較
        current_week = self._get_week_stats(0)
        previous_week = self._get_week_stats(1)
        
        if current_week and previous_week:
            # 成功率の変化
            success_rate_change = current_week['success_rate'] - previous_week['success_rate']
            print(f"成功率: {current_week['success_rate']:.1f}% ({success_rate_change:+.1f}%)")
            
            # 平均処理時間の変化
            if current_week['avg_time'] and previous_week['avg_time']:
                time_change = current_week['avg_time'] - previous_week['avg_time']
                print(f"平均処理時間: {current_week['avg_time']:.1f}秒 ({time_change:+.1f}秒)")
            
            # 記事数の変化
            if current_week['avg_articles'] and previous_week['avg_articles']:
                article_change = current_week['avg_articles'] - previous_week['avg_articles']
                print(f"平均検証記事数: {current_week['avg_articles']:.1f}件 ({article_change:+.1f}件)")
        else:
            print("前週との比較データが不足しています")
        
        print()
    
    def _get_week_stats(self, weeks_ago: int):
        """指定された週の統計を取得"""
        end_date = datetime.now() - timedelta(weeks=weeks_ago)
        start_date = end_date - timedelta(days=7)
        
        executions = 0
        successful = 0
        total_time = 0
        total_articles = 0
        
        for exec_data in self.anomaly_detector.execution_history:
            exec_time = datetime.fromisoformat(exec_data['timestamp'])
            if start_date <= exec_time < end_date:
                executions += 1
                if exec_data['success']:
                    successful += 1
                    total_time += exec_data['processing_time_seconds']
                    total_articles += exec_data['articles_verified']
        
        if executions == 0:
            return None
        
        return {
            'executions': executions,
            'successful': successful,
            'success_rate': (successful / executions * 100),
            'avg_time': (total_time / successful) if successful > 0 else None,
            'avg_articles': (total_articles / successful) if successful > 0 else None
        }
    
    def send_slack_dashboard(self):
        """Slack用ダッシュボードを送信"""
        # 統計情報を収集
        exec_stats = self.anomaly_detector.get_execution_stats()
        health_summary = self.health_checker.get_status_summary()
        recent_alerts = self.anomaly_detector.get_recent_alerts(hours=24)
        
        # メッセージ構築
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 AI News Feeder ダッシュボード"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*更新時刻:* {datetime.now().strftime('%Y/%m/%d %H:%M')}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # 実行統計セクション
        if exec_stats and 'recent_24h' in exec_stats:
            recent = exec_stats['recent_24h']
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*24時間の実行*\n{recent['total']}回"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*成功率*\n{recent['success_rate']:.1f}%"
                    }
                ]
            })
        
        # ヘルスステータス
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*システムヘルス*\n{health_summary.split('\\n')[0]}"
            }
        })
        
        # アラート情報
        alert_text = f"*最近24時間のアラート*\n"
        if recent_alerts:
            alert_text += f"⚠️ {len(recent_alerts)}件のアラート"
        else:
            alert_text += "✅ アラートなし"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": alert_text
            }
        })
        
        # 送信
        message = {
            "blocks": blocks,
            "text": "AI News Feeder ダッシュボード"
        }
        
        try:
            response = self.slack_notifier.session.post(
                self.slack_notifier.webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                print("Slackダッシュボード送信成功")
            else:
                print(f"Slack送信エラー: {response.status_code}")
                
        except Exception as e:
            print(f"Slack送信エラー: {e}")


def main():
    parser = argparse.ArgumentParser(description='実行統計レポート生成ツール')
    
    parser.add_argument('--daily', action='store_true',
                       help='日次レポートを生成')
    parser.add_argument('--weekly', action='store_true',
                       help='週次レポートを生成')
    parser.add_argument('--slack', action='store_true',
                       help='Slackダッシュボードを送信')
    
    args = parser.parse_args()
    
    reporter = StatisticsReporter()
    
    if args.daily:
        reporter.generate_daily_report()
    
    if args.weekly:
        reporter.generate_weekly_report()
    
    if args.slack:
        reporter.send_slack_dashboard()
    
    if not any([args.daily, args.weekly, args.slack]):
        # デフォルト: 日次レポート
        reporter.generate_daily_report()


if __name__ == "__main__":
    main()