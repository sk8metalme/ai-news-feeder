# AI News Feeder

Hacker Newsで話題のAI関連ニュースの信憑性を検証し、信頼できる情報をSlackに自動配信するPythonアプリケーション。

## 📊 機能概要

- **Hacker News監視**: AI関連キーワードでスコア上位記事を自動収集
- **ファクトチェック**: dev.to、Mediumで関連記事を検索し信憑性を検証
- **Slack自動投稿**: 検証済み記事を構造化フォーマットで通知
- **日次レポート**: JSON形式での詳細な分析レポートを生成
- **自動スケジューリング**: cron または内蔵スケジューラーで定期実行

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd ai-news-feeder

# Pythonの依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp env.example .env
# .envファイルを編集してSlack Webhook URLを設定
```

### 2. Slack Webhook設定

1. Slack Appを作成: https://api.slack.com/apps
2. Incoming Webhookを有効化
3. Webhook URLを`.env`ファイルに設定:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#ai-news
```

### 3. 実行方法

#### 単発実行（テスト用）
```bash
python main.py --run-once
```

#### スケジューラー実行
```bash
python main.py --schedule
```

#### cron設定（推奨）
```bash
./install_cron.sh
```

## 🧪 テスト実行

```bash
# 全テストを実行
python -m pytest tests/ -v

# または専用スクリプトを使用
./run_tests.py

# 特定のテストモジュールのみ実行
./run_tests.py hacker_news_api
```

### テスト統計
- **テスト数**: 56テスト
- **カバレッジ**: 主要機能をカバー
- **テスト種類**: 単体テスト、統合テスト、エラーハンドリング

## 📁 プロジェクト構造

```
ai-news-feeder/
├── main.py                 # メインエントリーポイント
├── requirements.txt        # Python依存関係
├── install_cron.sh        # cron設定スクリプト
├── run_tests.py           # テスト実行スクリプト
├── pytest.ini            # pytest設定
├── config/
│   └── settings.py        # 設定ファイル
├── src/
│   ├── api/
│   │   └── hacker_news.py # Hacker News API
│   ├── verification/
│   │   └── fact_checker.py # ファクトチェック機能
│   ├── notification/
│   │   └── slack_notifier.py # Slack通知
│   ├── utils/
│   │   ├── logger.py      # ログ機能
│   │   └── report_generator.py # レポート生成
│   └── scheduler.py       # スケジューラー
├── tests/                 # テストファイル
│   ├── conftest.py       # pytest設定とフィクスチャ
│   ├── test_*.py         # 各種テストファイル
├── logs/                 # ログファイル
├── data/                 # JSON レポート
└── .gitignore           # Git除外設定
```

## ⚙️ 設定

### キーワード設定
`config/settings.py`でAI関連キーワードをカスタマイズ可能:

```python
AI_KEYWORDS = [
    "ChatGPT", "Claude", "AI", "LLM", "OpenAI", "Google AI",
    "artificial intelligence", "machine learning", "deep learning"
]
```

### 検証設定
- **スコア閾値**: 50点以上のHacker News記事を対象
- **記事数制限**: 1日最大5件の記事を投稿
- **検証間隔**: 24時間ごとに実行

## 📈 投稿フォーマット

```
📊 AI News Verification Report
✅ Topic: ChatGPT-4o: The Next Generation of AI
🔗 Source: Hacker News (Score: 152)
📈 Verified: 3 related articles found
📚 Links: dev.to(2), Medium(1)
🌐 URL: https://example.com/article
⏰ Checked: 2025/01/05 09:00 JST
```

## 🔧 カスタマイズ

### 検証ロジックの調整
`src/verification/fact_checker.py`で検証条件を変更可能:

```python
# 検証合格条件を変更（現在: 1件以上の関連記事）
verification_status = "verified" if total_related >= 1 else "unverified"
```

### 通知フォーマットの変更
`src/notification/slack_notifier.py`でメッセージ形式をカスタマイズ:

```python
def format_verification_report(self, verification_result: Dict) -> str:
    # カスタムフォーマットを実装
```

## 📊 ログとレポート

### ログファイル
- 場所: `logs/ai_news_feeder_YYYYMMDD.log`
- レベル: INFO以上
- ローテーション: 日次

### JSONレポート
- 場所: `data/ai_news_report_YYYYMMDD.json`
- 内容: 検証結果の詳細データ
- 形式: 構造化JSON

## 🧪 テスト実行詳細

### テスト構成
- **設定テスト**: 12テスト - 設定値とenv変数のテスト
- **Hacker News API**: 10テスト - API通信、フィルタリング、エラー処理
- **ファクトチェッカー**: 10テスト - dev.to/Medium検索、検証ロジック
- **Slack通知**: 8テスト - メッセージフォーマット、通知送信
- **レポート生成**: 6テスト - JSON生成、統計計算、ファイル保存
- **スケジューラー**: 6テスト - ジョブ実行、エラーハンドリング、統合テスト
- **メインアプリ**: 5テスト - CLI引数、例外処理

### テスト実行例
```bash
# 全テスト実行
python -m pytest tests/ -v

# 特定モジュールのテスト
python -m pytest tests/test_hacker_news_api.py -v

# カバレッジレポート付き（pytest-covがインストールされている場合）
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## 🔍 トラブルシューティング

### よくある問題

1. **Slack通知が送信されない**
   - Webhook URLが正しく設定されているか確認
   - ネットワーク接続を確認

2. **記事が見つからない**
   - AI_KEYWORDSの設定を確認
   - SCORE_THRESHOLDを下げて試行

3. **外部API エラー**
   - レート制限に引っかかっている可能性
   - ログで詳細なエラーメッセージを確認

4. **テストの失敗**
   - 依存関係が正しくインストールされているか確認
   - `python -m pytest tests/ -v` でテスト実行

### ログレベルの変更
```python
# config/settings.py または直接コードで
logger.setLevel(logging.DEBUG)  # より詳細なログ
```

## 🛣️ 今後の開発予定

- [ ] Reddit API、GitHub Trending対応
- [ ] 3段階信憑性評価（高/中/低）
- [ ] Google Translate API連携での日本語対応
- [ ] Web UI での手動検証機能
- [ ] 統計分析とトレンド機能
- [ ] テストカバレッジの向上
- [ ] CI/CD パイプラインの構築

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

Issue報告やPull Requestを歓迎します。開発に参加する際は、以下の手順でお願いします:

1. Forkしてfeatureブランチを作成
2. 変更を実装
3. テストを実行: `./run_tests.py`
4. Pull Requestを作成

### 開発ガイドライン
- 新機能には必ずテストを追加
- コードスタイルは既存コードに合わせる
- ログメッセージは日本語と英語を適切に使い分ける

---

**注意**: 本ツールは個人使用を想定しています。大規模運用時は各APIの利用制限にご注意ください。