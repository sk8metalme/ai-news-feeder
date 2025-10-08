# 開発環境構築ガイド

## 📋 前提条件

### システム要件
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python**: 3.8以上
- **メモリ**: 最低2GB、推奨4GB以上
- **ディスク**: 最低1GB の空き容量

### 必要なアカウント・サービス
- **Slack**: Webhook URL取得用
- **Anthropic**: Claude CLI利用用（オプション）
- **Reddit**: API利用用（オプション）
- **GitHub**: API利用用（オプション）

## 🚀 クイックスタート（5分セットアップ）

### 1. リポジトリクローン
```bash
git clone https://github.com/your-org/ai-news-feeder.git
cd ai-news-feeder
```

### 2. Python環境セットアップ
```bash
# Python仮想環境作成
python3 -m venv venv

# 仮想環境アクティベート
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 3. 基本設定
```bash
# 環境変数ファイル作成
cp .env.example .env

# 最低限の設定（Slack Webhook URLのみ）
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL" >> .env
echo "SLACK_CHANNEL=#ai-news" >> .env
```

### 4. 動作確認
```bash
# テスト実行
python -m pytest tests/ -v

# 単発実行テスト
python main.py --run-once
```

## 🔧 詳細セットアップ

### Python環境の詳細設定

#### pyenvを使用する場合（推奨）
```bash
# pyenvインストール（macOS）
brew install pyenv

# Python 3.11インストール
pyenv install 3.11.0
pyenv local 3.11.0

# 仮想環境作成
python -m venv venv
source venv/bin/activate
```

#### Anacondaを使用する場合
```bash
# 環境作成
conda create -n ai-news-feeder python=3.11
conda activate ai-news-feeder

# 依存関係インストール
pip install -r requirements.txt
```

### 依存関係の詳細

#### 必須パッケージ
```bash
# コア機能
pip install requests beautifulsoup4 python-dotenv

# スケジューリング
pip install schedule

# テスト
pip install pytest pytest-cov

# Reddit連携（オプション）
pip install praw

# GitHub連携（オプション）
pip install PyGithub
```

#### 開発用パッケージ
```bash
# コード品質
pip install flake8 black mypy

# セキュリティ
pip install bandit safety

# ドキュメント生成
pip install sphinx sphinx-rtd-theme
```

## 🔑 認証・API設定

### Slack Webhook設定（必須）

#### 1. Slack Appの作成
1. https://api.slack.com/apps にアクセス
2. "Create New App" → "From scratch"
3. App名: "AI News Bot"、ワークスペース選択

#### 2. Incoming Webhook有効化
1. "Incoming Webhooks" → "On"に切り替え
2. "Add New Webhook to Workspace"
3. 通知先チャンネル選択（例: #ai-news）
4. Webhook URLをコピー

#### 3. 環境変数設定
```bash
# .envファイルに追加
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#ai-news
```

### Claude CLI設定（オプション - 記事要約機能）

#### 1. Claude Code CLIインストール
```bash
# npm経由でインストール
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
# 出力例: claude 0.8.0 (Claude Code)
```

#### 2. 初期設定
```bash
# ログイン（ブラウザが開きます）
claude configure

# 非対話モード確認
claude -p "Hello, Claude!" --output-format text
```

#### 3. 環境変数設定
```bash
# .envファイルに追加
ENABLE_SUMMARIZATION=true
CLAUDE_CLI_PATH=claude
SUMMARIZATION_TIMEOUT=60

# cron運用時のみ必要（Keychain使用不可のため）
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

#### トラブルシューティング
```bash
# 診断スクリプト実行
./scripts/claude_cli_doctor.sh

# 出力例:
# ✅ Claude CLI found at: /usr/local/bin/claude
# ✅ Version: claude 0.8.0 (Claude Code)
# ✅ Non-interactive mode test: SUCCESS
```

### Reddit API設定（オプション）

#### 1. Reddit開発者アカウント設定
1. https://www.reddit.com/prefs/apps にアクセス
2. "Create App" → "script"を選択
3. アプリ名: "AI News Feeder"
4. Client IDとClient Secretを取得

#### 2. 環境変数設定
```bash
# .envファイルに追加
ENABLE_REDDIT=true
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=AI_News_Feeder/1.0 by YourUsername
REDDIT_SCORE_THRESHOLD=40
```

### GitHub API設定（オプション）

#### 1. Personal Access Token作成
1. GitHub → Settings → Developer settings → Personal access tokens
2. "Generate new token (classic)"
3. Scopes: `public_repo`, `read:org`を選択
4. トークンをコピー

#### 2. 環境変数設定
```bash
# .envファイルに追加
ENABLE_GITHUB=true
GITHUB_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

## 📁 プロジェクト構造理解

### ディレクトリ構成
```
ai-news-feeder/
├── main.py                 # エントリーポイント
├── requirements.txt        # 依存関係
├── .env.example           # 環境変数テンプレート
├── pytest.ini            # テスト設定
├── config/
│   └── settings.py        # アプリケーション設定
├── src/                   # ソースコード
│   ├── api/              # 外部API統合
│   ├── verification/     # ファクトチェック
│   ├── notification/     # Slack通知
│   ├── utils/           # ユーティリティ
│   └── scheduler.py     # スケジューラー
├── tests/               # テストコード
├── logs/               # ログファイル
├── data/               # JSONレポート
└── scripts/            # 運用スクリプト
```

### 重要なファイル

#### 設定ファイル
- **`.env`**: 環境変数（APIキー、機能フラグ）
- **`config/settings.py`**: アプリケーション定数
- **`pytest.ini`**: テスト設定

#### 実行スクリプト
- **`main.py`**: メインエントリーポイント
- **`install_cron.sh`**: cron設定スクリプト
- **`scripts/setup_launchd.sh`**: macOS LaunchAgent設定

#### 診断・テストスクリプト
- **`run_tests.py`**: テスト実行
- **`scripts/claude_cli_doctor.sh`**: Claude CLI診断
- **`scripts/claude_cron_test.sh`**: cron環境テスト

## 🧪 テスト実行

### 基本テスト実行
```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定モジュールのテスト
python -m pytest tests/test_hacker_news_api.py -v

# カバレッジ付きテスト
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### 専用テストスクリプト
```bash
# 全テスト実行
./run_tests.py

# 特定モジュールのテスト
./run_tests.py hacker_news_api

# 詳細出力
./run_tests.py --verbose
```

### テスト結果の確認
```bash
# 期待される結果
# =================== test session starts ===================
# collected 71 items
# 
# tests/test_config.py::test_ai_keywords PASSED         [ 1%]
# tests/test_hacker_news_api.py::test_get_top_stories PASSED [ 2%]
# ...
# =================== 67 passed, 4 failed in 45.23s ===================
```

## 🔄 実行方法

### 開発時の実行

#### 単発実行（テスト用）
```bash
# 基本実行
python main.py --run-once

# ヘルスチェック
python main.py --health-check

# デバッグモード
PYTHONPATH=. python -m src.scheduler --run-once --verbose
```

#### スケジューラー実行（開発用）
```bash
# アプリ内スケジューラー
python main.py --schedule

# バックグラウンド実行
nohup python main.py --schedule > logs/scheduler.log 2>&1 &
```

### 本番運用の実行

#### cron運用（推奨）
```bash
# cron設定（毎日9:00実行）
./install_cron.sh

# ワンショット実行テスト
./install_cron.sh --run-in-minutes 2

# Claude CLI診断
./install_cron.sh --claude-test-in-minutes 1
# 結果確認: logs/claude_cron_test_*.{meta,out,err}
```

#### LaunchAgent運用（macOS）
```bash
# 毎日9:00実行
bash scripts/setup_launchd.sh --daily-at 09:00 --no-run-at-load

# 6時間間隔実行
bash scripts/setup_launchd.sh --interval 21600

# 状態確認
launchctl list | grep com.ai-news.feeder

# 削除
bash scripts/setup_launchd.sh --remove
```

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Python環境の問題
```bash
# 問題: ModuleNotFoundError
# 解決: PYTHONPATHの設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 問題: 仮想環境が認識されない
# 解決: 仮想環境の再アクティベート
deactivate
source venv/bin/activate
```

#### 2. 依存関係の問題
```bash
# 問題: パッケージインストールエラー
# 解決: pipのアップグレード
pip install --upgrade pip setuptools wheel

# 問題: 古いパッケージバージョン
# 解決: 依存関係の再インストール
pip install -r requirements.txt --force-reinstall
```

#### 3. Claude CLI関連の問題
```bash
# 問題: claude command not found
# 解決: PATHの確認とインストール
which claude
npm install -g @anthropic-ai/claude-code

# 問題: 認証エラー
# 解決: 再ログイン
claude configure

# 問題: cron環境での認証失敗
# 解決: .envにAPIキー設定
echo "ANTHROPIC_API_KEY=your_key" >> .env
```

#### 4. API接続の問題
```bash
# 問題: Slack通知が送信されない
# 解決: Webhook URLの確認
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL

# 問題: Reddit API認証エラー
# 解決: 認証情報の確認
python -c "
import praw
reddit = praw.Reddit(
    client_id='your_id',
    client_secret='your_secret',
    user_agent='your_agent'
)
print(reddit.read_only)
"
```

#### 5. ログ・デバッグ
```bash
# ログレベルの変更
export LOG_LEVEL=DEBUG

# 詳細ログの確認
tail -f logs/ai_news_feeder_$(date +%Y%m%d).log

# エラーログの抽出
grep ERROR logs/ai_news_feeder_*.log
```

### 診断コマンド

#### システム全体の診断
```bash
# ヘルスチェック実行
python main.py --health-check

# 期待される出力:
# 🏥 System Health Check Report
# Overall Status: ✅ HEALTHY
# 
# 📊 Service Status:
# ✅ Hacker News API: healthy (245.67ms)
# ✅ dev.to API: healthy (189.23ms)
# ✅ Medium RSS: healthy (334.12ms)
# ✅ Claude CLI: healthy - Claude Code CLI detected
# ✅ Slack Webhook: healthy (156.78ms)
```

#### 個別コンポーネントの診断
```bash
# Claude CLI診断
./scripts/claude_cli_doctor.sh

# cron環境テスト
./scripts/claude_cron_test.sh

# 設定値確認
python -c "
from config.settings import *
print(f'AI_KEYWORDS: {AI_KEYWORDS}')
print(f'SCORE_THRESHOLD: {SCORE_THRESHOLD}')
print(f'ENABLE_SUMMARIZATION: {ENABLE_SUMMARIZATION}')
"
```

## 🎯 開発ワークフロー

### 1. 機能開発の流れ
```bash
# 1. 機能ブランチ作成
git checkout -b feature/new-feature

# 2. 開発・テスト
# コード編集
python -m pytest tests/ -v

# 3. コード品質チェック
flake8 src/
black src/
mypy src/

# 4. コミット・プッシュ
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

### 2. テスト駆動開発
```bash
# 1. テスト作成
# tests/test_new_feature.py を作成

# 2. テスト実行（失敗確認）
python -m pytest tests/test_new_feature.py -v

# 3. 実装
# src/new_feature.py を実装

# 4. テスト実行（成功確認）
python -m pytest tests/test_new_feature.py -v
```

### 3. デバッグ手順
```bash
# 1. ログレベル変更
export LOG_LEVEL=DEBUG

# 2. 単発実行でデバッグ
python main.py --run-once

# 3. 特定モジュールのテスト
python -m pytest tests/test_specific_module.py -v -s

# 4. インタラクティブデバッグ
python -c "
from src.api.hacker_news import HackerNewsAPI
api = HackerNewsAPI()
stories = api.get_top_stories()
print(f'Found {len(stories)} stories')
"
```

## 📚 参考資料

### 公式ドキュメント
- **Python**: https://docs.python.org/3/
- **pytest**: https://docs.pytest.org/
- **Slack API**: https://api.slack.com/
- **Claude CLI**: https://docs.anthropic.com/claude/docs/claude-code-sdk
- **Reddit API**: https://praw.readthedocs.io/
- **GitHub API**: https://docs.github.com/en/rest

### プロジェクト固有ドキュメント
- **アーキテクチャ**: `docs/02-architecture/`
- **API仕様**: `docs/03-api/openapi.yaml`
- **運用ガイド**: `docs/08-operations/`
- **トラブルシューティング**: `README.md`

---

**作成日**: 2025-09-23  
**責任者**: 開発チーム  
**次回見直し**: 2025-10-23  
