# AI News Feeder 🤖📰

AI関連ニュースの信憑性を自動検証し、Slackに配信するボットです。

## 🎯 概要

AI News Feederは、Hacker Newsで話題のAI関連ニュースを自動的に収集し、dev.toやMediumで関連記事を検索して信憑性を検証します。検証済みの記事は構造化されたレポート形式でSlackに自動投稿されます。

## ✨ 主な機能

- **自動収集**: Hacker NewsからAI関連記事を毎日自動収集
- **信憑性検証**: dev.to、Mediumで関連記事を検索して検証
- **Slack通知**: 検証済み記事を美しいフォーマットで自動投稿
- **キーワードフィルタリング**: ChatGPT、Claude、AI、LLMなどのキーワードで絞り込み
- **スコアフィルタリング**: 高評価記事のみを選別（デフォルト: 50点以上）

## 🚀 クイックスタート

### 1. セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/ai-news-feeder.git
cd ai-news-feeder

# セットアップスクリプトの実行
chmod +x setup.sh
./setup.sh
```

### 2. 環境設定

`.env`ファイルを編集してSlack Webhook URLを設定:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 3. テスト実行

```bash
# 仮想環境を有効化
source venv/bin/activate

# テスト実行
python main.py
```

### 4. 定期実行の設定

```bash
# cronジョブの設定（毎日9時に実行）
./scripts/setup_cron.sh
```

## 📋 設定オプション

`.env`ファイルで以下の設定が可能です:

| 設定項目 | 説明 | デフォルト値 |
|---------|------|------------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | （必須） |
| `ARTICLES_PER_DAY` | 1日に投稿する記事数 | 5 |
| `MINIMUM_SCORE` | Hacker Newsの最低スコア | 50 |
| `RUN_HOUR` | 実行時刻（24時間形式） | 9 |

## 📊 投稿フォーマット

Slackに投稿される記事は以下のような形式です:

```
📊 AI News Verification Report
Date: 2025/09/05 09:00 JST
━━━━━━━━━━━━━━━━━━━━━━━━
Topic: ChatGPT-4o Achieves New Benchmark in Reasoning
Source: Hacker News (Score: 256)
✅ Verified: 3 related articles found
Links: dev.to(2), Medium(1)
URL: View Article
Checked: 2025/09/05 09:00 JST
━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🔍 検証ロジック

1. **記事収集**: Hacker News APIから過去24時間のトップ記事を取得
2. **AIフィルタリング**: タイトルにAI関連キーワードが含まれる記事を抽出
3. **スコアフィルタリング**: 設定されたスコア以上の記事のみを選択
4. **信憑性検証**: dev.toとMediumで関連記事を検索
5. **判定**: 1件以上の関連記事が見つかれば「検証済み」と判定

## 🛠️ 技術スタック

- **言語**: Python 3.x
- **主要ライブラリ**: 
  - requests: HTTP通信
  - beautifulsoup4: HTMLパース
  - feedparser: RSS解析
  - schedule: スケジューリング
- **外部API**:
  - Hacker News API
  - dev.to API
  - Medium RSS Feed

## 📁 プロジェクト構成

```
ai-news-feeder/
├── src/
│   ├── api/              # API クライアント
│   │   ├── hackernews_api.py
│   │   └── factcheck_api.py
│   ├── processing/       # メイン処理ロジック
│   │   └── news_processor.py
│   └── utils/           # ユーティリティ
│       ├── config.py
│       └── slack_notifier.py
├── scripts/             # 実行スクリプト
│   └── setup_cron.sh
├── reports/            # レポート保存用（自動生成）
├── logs/               # ログファイル（自動生成）
├── main.py             # エントリーポイント
├── requirements.txt    # 依存関係
├── setup.sh           # セットアップスクリプト
├── .env.example       # 環境変数サンプル
└── README.md          # このファイル
```

## 🔧 トラブルシューティング

### Slack通知が届かない
- `.env`ファイルのWebhook URLが正しいか確認
- Slackワークスペースの権限設定を確認

### 記事が見つからない
- AIキーワードの設定を確認（`src/utils/config.py`）
- スコア閾値を下げてみる（`MINIMUM_SCORE`）

### エラーログの確認
```bash
tail -f ai_news_feeder.log
```

## 🚧 今後の機能拡張予定

- [ ] Reddit API連携
- [ ] GitHub Trending連携
- [ ] 高度な信憑性判定（3段階評価）
- [ ] 日本語要約機能
- [ ] Web UI管理画面
- [ ] 複数チャンネル対応

## 📝 ライセンス

MIT License

## 🤝 コントリビューション

プルリクエストを歓迎します！大きな変更の場合は、まずissueを作成して変更内容について議論してください。

## 📧 お問い合わせ

質問や提案がある場合は、GitHubのissueを作成してください。