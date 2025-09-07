#!/bin/bash
# AI News Feederのcron設定スクリプト

# プロジェクトのパスを取得
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$(which python3)"

# cronジョブの定義（毎日9時に実行）
CRON_JOB="0 9 * * * cd $PROJECT_DIR && $PYTHON_PATH main.py >> $PROJECT_DIR/cron.log 2>&1"

# 現在のcrontabを取得
crontab -l > mycron 2>/dev/null || touch mycron

# 既存のAI News Feederジョブを削除
grep -v "AI News Feeder" mycron > temp && mv temp mycron

# 新しいジョブを追加
echo "# AI News Feeder - 毎日9時に実行" >> mycron
echo "$CRON_JOB" >> mycron

# crontabを更新
crontab mycron
rm mycron

echo "Cronジョブを設定しました:"
echo "$CRON_JOB"
echo ""
echo "現在のcrontab:"
crontab -l