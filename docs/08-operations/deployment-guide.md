# デプロイメントガイド

## 🚀 デプロイメント概要

AI News Feederは以下の方式でデプロイ可能です：

1. **ローカル実行**: 開発・テスト用
2. **cron運用**: 本番推奨方式
3. **LaunchAgent運用**: macOS専用
4. **Docker運用**: 将来実装予定
5. **クラウド運用**: 将来実装予定

## 📋 デプロイメント前チェックリスト

### 必須要件
- [ ] Python 3.8+ インストール済み
- [ ] 依存関係インストール済み（`pip install -r requirements.txt`）
- [ ] Slack Webhook URL設定済み
- [ ] 環境変数ファイル（`.env`）設定済み
- [ ] テスト成功確認（`python -m pytest tests/ -v`）

### オプション要件
- [ ] Claude CLI設定済み（要約機能用）
- [ ] Reddit API認証情報設定済み
- [ ] GitHub API認証情報設定済み
- [ ] ログディレクトリ作成済み（`logs/`）
- [ ] データディレクトリ作成済み（`data/`）

## 🔧 ローカル実行デプロイ

### 開発・テスト用実行
```bash
# 単発実行
python main.py --run-once

# スケジューラー実行
python main.py --schedule

# ヘルスチェック
python main.py --health-check
```

### バックグラウンド実行
```bash
# nohupを使用
nohup python main.py --schedule > logs/scheduler.log 2>&1 &

# プロセス確認
ps aux | grep "python main.py"

# プロセス終了
kill <PID>
```

## ⏰ cron運用デプロイ（推奨）

### 自動設定スクリプト使用
```bash
# 基本設定（毎日9:00実行）
./install_cron.sh

# カスタム時刻設定
./install_cron.sh --time "0 6 * * *"  # 毎日6:00実行

# 設定確認
crontab -l
```

### 手動cron設定
```bash
# crontab編集
crontab -e

# 以下を追加（毎日9:00実行）
0 9 * * * cd /path/to/ai-news-feeder && /path/to/python main.py --run-once >> logs/cron.log 2>&1
```

### cron環境の注意点
```bash
# 環境変数の設定
# crontabの先頭に追加
PATH=/usr/local/bin:/usr/bin:/bin
LANG=ja_JP.UTF-8
PYTHONPATH=/path/to/ai-news-feeder

# .envファイルの読み込み確認
# install_cron.shが自動で設定
```

### cron運用の診断
```bash
# ワンショット実行テスト
./install_cron.sh --run-in-minutes 2

# Claude CLI診断
./install_cron.sh --claude-test-in-minutes 1

# 結果確認
ls -la logs/claude_cron_test_*
cat logs/claude_cron_test_*.meta
```

## 🍎 LaunchAgent運用デプロイ（macOS）

### 基本設定
```bash
# 毎日9:00実行
bash scripts/setup_launchd.sh --daily-at 09:00 --no-run-at-load

# 6時間間隔実行
bash scripts/setup_launchd.sh --interval 21600

# 即座に実行開始
bash scripts/setup_launchd.sh --daily-at 09:00
```

### LaunchAgent管理
```bash
# 状態確認
launchctl list | grep com.ai-news.feeder

# 手動実行
launchctl start com.ai-news.feeder.daily

# 停止
launchctl stop com.ai-news.feeder.daily

# 削除
bash scripts/setup_launchd.sh --remove
```

### LaunchAgentの利点
- **Keychain認証**: APIキーを`.env`に保存不要
- **ユーザーセッション**: GUI環境での実行
- **自動復旧**: システム再起動時の自動開始

## 🐳 Docker運用デプロイ（将来実装）

### Dockerfile例
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py", "--schedule"]
```

### docker-compose.yml例
```yaml
version: '3.8'
services:
  ai-news-feeder:
    build: .
    environment:
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - ENABLE_SUMMARIZATION=${ENABLE_SUMMARIZATION}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
```

## ☁️ クラウド運用デプロイ（将来実装）

### AWS Lambda
```bash
# デプロイパッケージ作成
pip install -r requirements.txt -t package/
cp -r src/ package/
cd package && zip -r ../deployment.zip .

# Lambda関数作成
aws lambda create-function \
  --function-name ai-news-feeder \
  --runtime python3.11 \
  --zip-file fileb://deployment.zip
```

### Google Cloud Functions
```bash
# デプロイ
gcloud functions deploy ai-news-feeder \
  --runtime python311 \
  --trigger-http \
  --entry-point main
```

### Azure Functions
```bash
# 関数アプリ作成
func init ai-news-feeder --python
func new --name ai-news-feeder --template "Timer trigger"
```

## 📊 デプロイメント監視

### ログ監視
```bash
# リアルタイムログ監視
tail -f logs/ai_news_feeder_$(date +%Y%m%d).log

# エラーログ抽出
grep ERROR logs/ai_news_feeder_*.log | tail -20

# 統計情報確認
grep "Processing completed" logs/ai_news_feeder_*.log | tail -10
```

### ヘルスチェック
```bash
# 定期ヘルスチェック
python main.py --health-check

# 自動ヘルスチェック（cron）
# crontabに追加
*/30 * * * * cd /path/to/ai-news-feeder && python main.py --health-check >> logs/health.log 2>&1
```

### パフォーマンス監視
```bash
# 処理時間監視
grep "Processing time" logs/ai_news_feeder_*.log | awk '{print $NF}' | sort -n

# メモリ使用量監視
ps aux | grep "python main.py" | awk '{print $4}'

# ディスク使用量監視
du -sh logs/ data/
```

## 🔧 設定管理

### 環境別設定

#### 開発環境（.env.development）
```env
# 開発用設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/DEV/WEBHOOK/URL
SLACK_CHANNEL=#ai-news-dev
MAX_ARTICLES_PER_SOURCE=3
ENABLE_SUMMARIZATION=false
LOG_LEVEL=DEBUG
```

#### 本番環境（.env.production）
```env
# 本番用設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/PROD/WEBHOOK/URL
SLACK_CHANNEL=#ai-news
MAX_ARTICLES_PER_SOURCE=5
ENABLE_SUMMARIZATION=true
LOG_LEVEL=INFO
```

#### ステージング環境（.env.staging）
```env
# ステージング用設定
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/STAGING/WEBHOOK/URL
SLACK_CHANNEL=#ai-news-staging
MAX_ARTICLES_PER_SOURCE=5
ENABLE_SUMMARIZATION=true
LOG_LEVEL=INFO
```

### 設定の切り替え
```bash
# 環境別実行
ENV=development python main.py --run-once
ENV=production python main.py --run-once
ENV=staging python main.py --run-once
```

## 🛡️ セキュリティ考慮事項

### 認証情報管理
```bash
# .envファイルの権限設定
chmod 600 .env

# 機密情報の確認
grep -E "(KEY|SECRET|TOKEN|PASSWORD)" .env

# 環境変数の暗号化（本番環境）
# 外部キー管理サービスの使用を推奨
```

### ファイアウォール設定
```bash
# 必要なポートのみ開放
# HTTP/HTTPS: 80, 443（外部API通信用）
# SSH: 22（管理用）

# 不要なポートの閉鎖確認
netstat -tuln | grep LISTEN
```

### ログセキュリティ
```bash
# ログファイルの権限設定
chmod 640 logs/*.log

# 機密情報のログ出力防止確認
grep -E "(password|secret|token)" logs/*.log
```

## 🔄 デプロイメント自動化

### GitHub Actions（CI/CD）
```yaml
name: Deploy AI News Feeder

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: python -m pytest tests/ -v
    
    - name: Deploy to server
      run: |
        # デプロイスクリプト実行
        ./scripts/deploy.sh
```

### デプロイスクリプト例
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

echo "🚀 Starting deployment..."

# バックアップ作成
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 最新コード取得
git pull origin main

# 依存関係更新
pip install -r requirements.txt

# テスト実行
python -m pytest tests/ -v

# cron設定更新
./install_cron.sh

echo "✅ Deployment completed successfully"
```

## 📋 デプロイメント後チェックリスト

### 即座に確認すべき項目
- [ ] アプリケーションが正常に起動する
- [ ] ヘルスチェックが成功する
- [ ] ログファイルが正常に出力される
- [ ] Slack通知が送信される
- [ ] 外部API接続が正常

### 24時間後に確認すべき項目
- [ ] スケジュール実行が正常に動作
- [ ] ログローテーションが正常
- [ ] メモリリークが発生していない
- [ ] エラー率が許容範囲内
- [ ] パフォーマンスが期待値内

### 1週間後に確認すべき項目
- [ ] 継続的な安定動作
- [ ] ディスク使用量の増加傾向
- [ ] 外部API制限に抵触していない
- [ ] 通知品質が維持されている
- [ ] ユーザーフィードバックが良好

## 🆘 トラブルシューティング

### よくあるデプロイエラー

#### 1. 依存関係エラー
```bash
# 問題: ModuleNotFoundError
# 解決: 依存関係の再インストール
pip install -r requirements.txt --force-reinstall

# 仮想環境の確認
which python
pip list
```

#### 2. 権限エラー
```bash
# 問題: Permission denied
# 解決: ファイル権限の修正
chmod +x install_cron.sh
chmod +x scripts/*.sh

# ディレクトリ権限の確認
ls -la logs/ data/
```

#### 3. 環境変数エラー
```bash
# 問題: 環境変数が読み込まれない
# 解決: .envファイルの確認
cat .env
python -c "import os; print(os.getenv('SLACK_WEBHOOK_URL'))"
```

#### 4. cron実行エラー
```bash
# 問題: cronで実行されない
# 解決: cron設定の確認
crontab -l
grep CRON /var/log/syslog

# 環境変数の確認
./install_cron.sh --claude-test-in-minutes 1
```

### ロールバック手順
```bash
# 1. 前バージョンへの復帰
git checkout <previous-commit>

# 2. 設定ファイルの復元
cp .env.backup.<timestamp> .env

# 3. 依存関係の復元
pip install -r requirements.txt

# 4. サービス再起動
./install_cron.sh

# 5. 動作確認
python main.py --health-check
```

---

**作成日**: 2025-09-23  
**責任者**: 運用チーム  
**次回見直し**: 2025-10-23  
