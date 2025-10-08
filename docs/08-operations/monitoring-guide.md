# 監視・運用ガイド

## 📊 監視概要

AI News Feederの安定運用のための包括的な監視戦略とベストプラクティスを提供します。

### 監視対象
- **アプリケーション**: 処理成功率、実行時間、エラー率
- **外部API**: 接続状況、レスポンス時間、レート制限
- **システムリソース**: CPU、メモリ、ディスク使用量
- **データ品質**: 記事収集数、検証率、要約成功率

## 🎯 監視指標（KPI）

### アプリケーション指標

#### 成功率指標
```
記事収集成功率 = 成功した記事収集数 / 総試行数 × 100
目標値: 95%以上

検証成功率 = 検証完了記事数 / 収集記事数 × 100
目標値: 90%以上

要約成功率 = 要約生成成功数 / 要約試行数 × 100
目標値: 80%以上

通知送信成功率 = 送信成功数 / 送信試行数 × 100
目標値: 98%以上
```

#### パフォーマンス指標
```
平均処理時間 = 総処理時間 / 処理記事数
目標値: 記事あたり60秒以内

API応答時間 = API呼び出し完了時間 - 開始時間
目標値: 各API 5秒以内

システム稼働率 = 正常実行時間 / 総実行時間 × 100
目標値: 99%以上
```

### 品質指標
```
記事品質スコア = 検証済み記事数 / 総記事数 × 100
目標値: 70%以上

重複除去効率 = 除去された重複記事数 / 収集前記事数 × 100
目標値: 10%以上

キーワード適合率 = AI関連記事数 / 総収集記事数 × 100
目標値: 85%以上
```

## 🔍 監視方法

### 1. ヘルスチェック監視

#### 自動ヘルスチェック
```bash
# crontabに追加（30分間隔）
*/30 * * * * cd /path/to/ai-news-feeder && python main.py --health-check >> logs/health.log 2>&1

# ヘルスチェック結果の確認
tail -f logs/health.log
```

#### ヘルスチェック項目
```python
# 監視対象サービス
services = [
    "hacker_news_api",      # Hacker News API接続
    "dev_to_api",          # dev.to API接続
    "medium_rss",          # Medium RSS接続
    "claude_cli",          # Claude CLI可用性
    "slack_webhook",       # Slack Webhook接続
    "system_resources"     # システムリソース
]

# 各サービスの状態
# healthy: 正常
# degraded: 劣化（警告レベル）
# unhealthy: 異常（エラーレベル）
```

### 2. ログ監視

#### ログファイル構成
```
logs/
├── ai_news_feeder_YYYYMMDD.log    # 日次アプリケーションログ
├── health.log                      # ヘルスチェックログ
├── cron.log                       # cron実行ログ
├── claude_cron_test_*.{meta,out,err}  # Claude CLI診断ログ
└── launchd.{out,err}.log          # LaunchAgent実行ログ
```

#### ログ監視コマンド
```bash
# リアルタイムログ監視
tail -f logs/ai_news_feeder_$(date +%Y%m%d).log

# エラーログ抽出
grep -i error logs/ai_news_feeder_*.log | tail -20

# 警告ログ抽出
grep -i warning logs/ai_news_feeder_*.log | tail -20

# 処理統計の確認
grep "Processing completed" logs/ai_news_feeder_*.log | tail -10

# Claude CLI関連エラー
grep -i "claude" logs/ai_news_feeder_*.log | grep -i error
```

#### ログアラート設定
```bash
# エラー検知スクリプト
#!/bin/bash
# scripts/log_monitor.sh

LOG_FILE="logs/ai_news_feeder_$(date +%Y%m%d).log"
ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo 0)

if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "⚠️ High error count detected: $ERROR_COUNT errors"
    # Slack通知やメール送信
fi
```

### 3. パフォーマンス監視

#### 処理時間監視
```bash
# 処理時間の統計
grep "Processing time:" logs/ai_news_feeder_*.log | \
awk '{print $NF}' | \
awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# 処理時間の分布
grep "Processing time:" logs/ai_news_feeder_*.log | \
awk '{print $NF}' | sort -n | \
awk '{
    if ($1 < 60) fast++
    else if ($1 < 180) normal++
    else slow++
}
END {
    print "Fast (<60s):", fast
    print "Normal (60-180s):", normal  
    print "Slow (>180s):", slow
}'
```

#### リソース使用量監視
```bash
# メモリ使用量監視
ps aux | grep "python main.py" | awk '{print $4}' | head -1

# ディスク使用量監視
du -sh logs/ data/

# システムリソース監視スクリプト
#!/bin/bash
# scripts/resource_monitor.sh

MEMORY_USAGE=$(ps aux | grep "python main.py" | awk '{sum+=$4} END {print sum}')
DISK_LOGS=$(du -sm logs/ | awk '{print $1}')
DISK_DATA=$(du -sm data/ | awk '{print $1}')

echo "Memory Usage: ${MEMORY_USAGE}%"
echo "Logs Directory: ${DISK_LOGS}MB"
echo "Data Directory: ${DISK_DATA}MB"

# アラート閾値チェック
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "⚠️ High memory usage: ${MEMORY_USAGE}%"
fi
```

### 4. 外部API監視

#### API応答時間監視
```bash
# Hacker News API監視
curl -w "@curl-format.txt" -o /dev/null -s "https://hacker-news.firebaseio.com/v0/topstories.json"

# curl-format.txt
time_namelookup:  %{time_namelookup}\n
time_connect:     %{time_connect}\n
time_appconnect:  %{time_appconnect}\n
time_pretransfer: %{time_pretransfer}\n
time_redirect:    %{time_redirect}\n
time_starttransfer: %{time_starttransfer}\n
time_total:       %{time_total}\n
```

#### API制限監視
```python
# Reddit API制限監視
import praw

reddit = praw.Reddit(...)
print(f"Remaining requests: {reddit.auth.limits}")

# GitHub API制限監視
import github

g = github.Github("token")
rate_limit = g.get_rate_limit()
print(f"Core remaining: {rate_limit.core.remaining}")
print(f"Reset time: {rate_limit.core.reset}")
```

## 📈 監視ダッシュボード

### 日次レポート監視
```bash
# 日次レポート確認
python -c "
import json
from datetime import date

report_file = f'data/ai_news_report_{date.today().strftime(\"%Y%m%d\")}.json'
try:
    with open(report_file) as f:
        data = json.load(f)
    
    print(f'📊 Daily Report Summary')
    print(f'Total Articles: {data.get(\"total_articles\", 0)}')
    print(f'Verified Articles: {data.get(\"verified_articles\", 0)}')
    print(f'Processing Time: {data.get(\"processing_time\", 0):.1f}s')
    print(f'Success Rate: {data.get(\"success_rate\", 0):.1%}')
except FileNotFoundError:
    print('❌ Daily report not found')
"
```

### 週次統計レポート
```bash
#!/bin/bash
# scripts/weekly_report.sh

echo "📊 Weekly Statistics Report"
echo "=========================="

# 過去7日間のログファイル
for i in {0..6}; do
    DATE=$(date -d "$i days ago" +%Y%m%d)
    LOG_FILE="logs/ai_news_feeder_$DATE.log"
    
    if [ -f "$LOG_FILE" ]; then
        ARTICLES=$(grep -c "Processing article" "$LOG_FILE" 2>/dev/null || echo 0)
        ERRORS=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo 0)
        echo "$DATE: Articles=$ARTICLES, Errors=$ERRORS"
    fi
done

# 週間統計
TOTAL_ARTICLES=$(grep -c "Processing article" logs/ai_news_feeder_*.log 2>/dev/null || echo 0)
TOTAL_ERRORS=$(grep -c "ERROR" logs/ai_news_feeder_*.log 2>/dev/null || echo 0)

echo "=========================="
echo "Total Articles: $TOTAL_ARTICLES"
echo "Total Errors: $TOTAL_ERRORS"
echo "Error Rate: $(echo "scale=2; $TOTAL_ERRORS * 100 / $TOTAL_ARTICLES" | bc)%"
```

## 🚨 アラート設定

### 1. エラー率アラート
```bash
#!/bin/bash
# scripts/error_alert.sh

THRESHOLD=5  # エラー閾値
LOG_FILE="logs/ai_news_feeder_$(date +%Y%m%d).log"

if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE")
    
    if [ "$ERROR_COUNT" -gt "$THRESHOLD" ]; then
        MESSAGE="🚨 High error rate detected: $ERROR_COUNT errors in $(basename $LOG_FILE)"
        
        # Slack通知
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$MESSAGE\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
fi
```

### 2. 処理時間アラート
```bash
#!/bin/bash
# scripts/performance_alert.sh

THRESHOLD=300  # 5分閾値（秒）
LOG_FILE="logs/ai_news_feeder_$(date +%Y%m%d).log"

if [ -f "$LOG_FILE" ]; then
    LAST_PROCESSING_TIME=$(grep "Processing time:" "$LOG_FILE" | tail -1 | awk '{print $NF}')
    
    if (( $(echo "$LAST_PROCESSING_TIME > $THRESHOLD" | bc -l) )); then
        MESSAGE="⏰ Slow processing detected: ${LAST_PROCESSING_TIME}s (threshold: ${THRESHOLD}s)"
        
        # Slack通知
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$MESSAGE\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
fi
```

### 3. 連続失敗アラート
```bash
#!/bin/bash
# scripts/failure_alert.sh

FAILURE_THRESHOLD=3
LOG_FILES=($(ls -t logs/ai_news_feeder_*.log | head -$FAILURE_THRESHOLD))

CONSECUTIVE_FAILURES=0
for LOG_FILE in "${LOG_FILES[@]}"; do
    if grep -q "Processing failed" "$LOG_FILE"; then
        ((CONSECUTIVE_FAILURES++))
    else
        break
    fi
done

if [ "$CONSECUTIVE_FAILURES" -ge "$FAILURE_THRESHOLD" ]; then
    MESSAGE="🔥 $CONSECUTIVE_FAILURES consecutive failures detected. System may be down."
    
    # 緊急通知
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$MESSAGE\", \"channel\":\"#alerts\"}" \
        "$SLACK_WEBHOOK_URL"
fi
```

## 📊 監視自動化

### cron監視スケジュール
```bash
# crontab -e に追加

# ヘルスチェック（30分間隔）
*/30 * * * * cd /path/to/ai-news-feeder && python main.py --health-check >> logs/health.log 2>&1

# エラー監視（1時間間隔）
0 * * * * /path/to/ai-news-feeder/scripts/error_alert.sh

# パフォーマンス監視（1時間間隔）
0 * * * * /path/to/ai-news-feeder/scripts/performance_alert.sh

# 連続失敗監視（30分間隔）
*/30 * * * * /path/to/ai-news-feeder/scripts/failure_alert.sh

# 週次レポート（月曜日9:00）
0 9 * * 1 /path/to/ai-news-feeder/scripts/weekly_report.sh

# ログローテーション（日次0:00）
0 0 * * * find /path/to/ai-news-feeder/logs -name "*.log" -mtime +30 -delete
```

### 監視ダッシュボードスクリプト
```bash
#!/bin/bash
# scripts/monitoring_dashboard.sh

clear
echo "🖥️  AI News Feeder Monitoring Dashboard"
echo "========================================"
echo "Last updated: $(date)"
echo

# システム状態
echo "📊 System Status:"
python main.py --health-check | grep -E "(Overall Status|Service Status)" -A 10

echo
echo "📈 Recent Performance:"

# 最新の処理統計
LATEST_LOG=$(ls -t logs/ai_news_feeder_*.log | head -1)
if [ -f "$LATEST_LOG" ]; then
    echo "Latest log: $(basename $LATEST_LOG)"
    
    # 処理記事数
    ARTICLES=$(grep -c "Processing article" "$LATEST_LOG" 2>/dev/null || echo 0)
    echo "Articles processed: $ARTICLES"
    
    # エラー数
    ERRORS=$(grep -c "ERROR" "$LATEST_LOG" 2>/dev/null || echo 0)
    echo "Errors: $ERRORS"
    
    # 最新の処理時間
    LAST_TIME=$(grep "Processing time:" "$LATEST_LOG" | tail -1 | awk '{print $NF}' 2>/dev/null || echo "N/A")
    echo "Last processing time: ${LAST_TIME}s"
fi

echo
echo "💾 Resource Usage:"

# ディスク使用量
LOGS_SIZE=$(du -sh logs/ 2>/dev/null | awk '{print $1}' || echo "N/A")
DATA_SIZE=$(du -sh data/ 2>/dev/null | awk '{print $1}' || echo "N/A")
echo "Logs directory: $LOGS_SIZE"
echo "Data directory: $DATA_SIZE"

# プロセス確認
if pgrep -f "python main.py" > /dev/null; then
    echo "✅ Process running"
else
    echo "❌ Process not running"
fi

echo
echo "🔄 Recent Activity:"
tail -5 "$LATEST_LOG" 2>/dev/null || echo "No recent activity"
```

## 🛠️ トラブルシューティング

### 監視アラートへの対応

#### 高エラー率の対応
```bash
# 1. エラーログの詳細確認
grep "ERROR" logs/ai_news_feeder_$(date +%Y%m%d).log | tail -10

# 2. 外部API状態確認
python main.py --health-check

# 3. 設定ファイル確認
cat .env | grep -E "(URL|KEY|TOKEN)"

# 4. 必要に応じて再起動
# cron運用の場合は次回実行を待つ
# LaunchAgent運用の場合
launchctl restart com.ai-news.feeder.daily
```

#### 処理時間遅延の対応
```bash
# 1. 処理時間の詳細分析
grep "Processing time:" logs/ai_news_feeder_*.log | \
awk '{print $NF}' | sort -n | tail -10

# 2. Claude CLI応答時間確認
time claude -p "test" --output-format text

# 3. ネットワーク接続確認
curl -w "%{time_total}" -o /dev/null -s https://hacker-news.firebaseio.com/v0/topstories.json

# 4. システムリソース確認
top -p $(pgrep -f "python main.py")
```

#### 連続失敗の対応
```bash
# 1. 最新のエラー詳細確認
tail -50 logs/ai_news_feeder_$(date +%Y%m%d).log

# 2. 設定ファイルの整合性確認
python -c "
from config.settings import *
print('SLACK_WEBHOOK_URL:', bool(SLACK_WEBHOOK_URL))
print('AI_KEYWORDS:', len(AI_KEYWORDS))
print('ENABLE_SUMMARIZATION:', ENABLE_SUMMARIZATION)
"

# 3. 依存関係の確認
pip check

# 4. 手動実行テスト
python main.py --run-once --verbose
```

## 📋 監視チェックリスト

### 日次チェック項目
- [ ] ヘルスチェック結果確認
- [ ] エラーログ確認
- [ ] 処理統計確認
- [ ] Slack通知送信確認
- [ ] ディスク使用量確認

### 週次チェック項目
- [ ] 週間統計レポート確認
- [ ] パフォーマンストレンド分析
- [ ] ログファイルのローテーション
- [ ] 設定ファイルのバックアップ
- [ ] 依存関係の更新確認

### 月次チェック項目
- [ ] 全体的なパフォーマンス評価
- [ ] 監視閾値の見直し
- [ ] アラート設定の最適化
- [ ] ドキュメントの更新
- [ ] セキュリティ設定の確認

---

**作成日**: 2025-09-23  
**責任者**: 運用チーム  
**次回見直し**: 2025-10-23  
