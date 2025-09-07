# 機能仕様書: Reddit API & GitHub Trending連携

**Feature ID**: 001-reddit-api-github  
**作成日**: 2025-09-07  
**最終更新**: 2025-09-07  
**Phase**: 3 (機能拡張)

## 📋 概要

AI News FeederにReddit APIとGitHub Trending APIとの連携機能を追加し、情報源を拡張してより包括的なAI関連ニュース収集を実現する。

### 目的
- Hacker Newsに加えてReddit、GitHub TrendingからもAI関連情報を収集
- 多様な情報源から最新のAI技術トレンドを把握
- 統合された検証・要約・通知システムを提供

### スコープ
- **Phase 3.1**: Reddit API連携実装 (14日間)
- **Phase 3.2**: GitHub Trending連携実装 (14日間)  
- **Phase 3.3**: 統合・最適化 (7日間)

## 🎯 要件定義

### 機能要件

#### 1. Reddit API連携機能
- **監視対象Subreddit**:
  - r/MachineLearning
  - r/artificial
  - r/singularity
  - r/MachineLearningNews
- **取得データ**:
  - 投稿タイトル・本文
  - スコア・コメント数
  - 投稿者・投稿時刻
  - URL・フレア情報
- **フィルタリング条件**:
  - AI関連キーワードマッチング
  - スコア閾値 (50以上)
  - 投稿時間 (24時間以内)

#### 2. GitHub Trending連携機能
- **監視対象言語**:
  - Python
  - JavaScript
  - TypeScript
  - Jupyter Notebook
- **監視対象トピック**:
  - machine-learning
  - artificial-intelligence
  - deep-learning
  - nlp
- **取得データ**:
  - リポジトリ名・説明
  - Star数・今日のStar増加数
  - 言語・トピック
  - README概要
- **フィルタリング条件**:
  - AI関連トピック必須
  - 今日のStar増加数 10以上
  - リポジトリサイズ適正

#### 3. 統合機能
- **統合データ形式**: 共通のArticleクラスで正規化
- **重複除去**: URL・タイトル類似度による重複検知
- **優先度管理**: ソース別・スコア別の優先度設定
- **統合レポート**: 3ソース統合の日次レポート生成

### 非機能要件

#### 1. パフォーマンス
- **処理時間**: 3ソース合計で10分以内
- **API制限対応**:
  - Reddit: 60req/分制限対応
  - GitHub: 5,000req/時制限対応
- **並列処理**: 3ソースの並行取得

#### 2. 信頼性
- **エラーハンドリング**: 各API失敗時の継続処理
- **レート制限**: 指数バックオフ・リトライ実装
- **フォールバック**: 部分的失敗時の動作継続

#### 3. 保守性
- **設定の外部化**: 監視対象・条件の設定ファイル化
- **ログの詳細化**: ソース別の詳細ログ
- **テスタビリティ**: ソース別の独立テスト可能

## 🏗️ 技術設計

### アーキテクチャ

```
src/
├── api/
│   ├── reddit_api.py          # Reddit API客户端
│   ├── github_trending.py     # GitHub Trending API客户端
│   └── hacker_news.py         # 既存のHacker News API
├── processing/
│   ├── reddit_processor.py    # Reddit記事処理
│   ├── github_processor.py    # GitHub repository処理
│   └── unified_processor.py   # 統合処理
├── orchestrator/
│   └── news_orchestrator.py   # 3ソース統合管理
└── utils/
    ├── deduplication.py       # 重複除去
    └── unified_report_generator.py # 統合レポート
```

### データフロー

1. **並列データ取得**
   ```
   Reddit API ─┐
   GitHub API ─┼─→ Unified Processor → Fact Checker → Slack Notifier
   Hacker News ─┘
   ```

2. **データ正規化**
   ```python
   @dataclass
   class Article:
       source: str  # "reddit", "github", "hackernews"
       title: str
       content: str
       url: str
       score: int
       timestamp: datetime
       source_specific: Dict[str, Any]
   ```

### API仕様

#### Reddit API連携
```python
class RedditAPI:
    def __init__(self, client_id: str, client_secret: str)
    def get_subreddit_posts(self, subreddit: str, limit: int = 10) -> List[RedditPost]
    def filter_ai_related(self, posts: List[RedditPost]) -> List[RedditPost]
```

#### GitHub Trending連携
```python
class GitHubTrendingAPI:
    def __init__(self, access_token: str)
    def get_trending_repos(self, language: str, since: str = "daily") -> List[Repository]
    def get_repo_details(self, repo_name: str) -> Repository
    def filter_ai_repos(self, repos: List[Repository]) -> List[Repository]
```

## 🧪 テスト戦略

### テスト構成
1. **単体テスト** (各API層): 20テスト
2. **統合テスト** (プロセッサー): 15テスト
3. **エンドツーエンドテスト** (全体フロー): 10テスト
4. **パフォーマンステスト** (負荷・速度): 5テスト

### テスト項目

#### Reddit API テスト
- [ ] OAuth認証テスト
- [ ] Subreddit取得テスト
- [ ] フィルタリングテスト
- [ ] レート制限対応テスト
- [ ] エラーハンドリングテスト

#### GitHub API テスト
- [ ] Personal Access Token認証テスト
- [ ] Trending取得テスト
- [ ] Repository詳細取得テスト
- [ ] AI関連フィルタリングテスト
- [ ] レート制限対応テスト

#### 統合テスト
- [ ] 3ソース並列処理テスト
- [ ] 重複除去テスト
- [ ] 統合レポート生成テスト
- [ ] エラー時の部分動作テスト

## 📊 実装計画

### Phase 3.1: Reddit API連携 (14日間)

#### Week 1 (Day 1-7)
- **Day 1-2**: Reddit開発者アカウント取得・API調査
- **Day 3-4**: `src/api/reddit_api.py` 基本実装
- **Day 5-6**: `src/processing/reddit_processor.py` 実装
- **Day 7**: ユニットテスト作成

#### Week 2 (Day 8-14)
- **Day 8-9**: ファクトチェック統合・エラーハンドリング
- **Day 10-11**: 統合テスト・デバッグ
- **Day 12-13**: パフォーマンステスト・最適化
- **Day 14**: Sprint 5完了・レビュー

### Phase 3.2: GitHub Trending連携 (14日間)

#### Week 1 (Day 15-21)
- **Day 15-16**: GitHub Personal Access Token設定・API調査
- **Day 17-18**: `src/api/github_trending.py` 基本実装
- **Day 19-20**: `src/processing/github_processor.py` 実装
- **Day 21**: ユニットテスト作成

#### Week 2 (Day 22-28)
- **Day 22-23**: Claude CLI要約機能統合
- **Day 24-25**: 統合テスト・パフォーマンステスト
- **Day 26-27**: ドキュメント作成・最終テスト
- **Day 28**: Sprint 6完了・統合テスト

### Phase 3.3: 統合・最適化 (7日間)

#### 統合作業 (Day 29-35)
- **Day 29-31**: 統合管理システム実装
  - `src/orchestrator/news_orchestrator.py`
  - `src/utils/deduplication.py`
  - `src/utils/unified_report_generator.py`
- **Day 32-33**: パフォーマンス最適化
  - 非同期処理導入
  - 並列処理最適化
  - キャッシュ機能拡張
- **Day 34-35**: 最終テスト・文書化
  - エンドツーエンドテスト
  - 運用マニュアル更新
  - v1.3.0リリース準備

## 🔧 設定項目

### 環境変数
```env
# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=ai-news-feeder/1.0

# GitHub API
GITHUB_ACCESS_TOKEN=your_github_personal_access_token

# 統合設定
ENABLE_REDDIT=true
ENABLE_GITHUB=true
MAX_ARTICLES_PER_SOURCE=5
```

### 設定ファイル (config/sources.py)
```python
REDDIT_SUBREDDITS = [
    "MachineLearning",
    "artificial", 
    "singularity",
    "MachineLearningNews"
]

GITHUB_LANGUAGES = [
    "Python",
    "JavaScript", 
    "TypeScript",
    "Jupyter Notebook"
]

GITHUB_TOPICS = [
    "machine-learning",
    "artificial-intelligence",
    "deep-learning",
    "nlp"
]
```

## 📈 成功指標

### 技術指標
- **テスト成功率**: 95%以上
- **処理時間**: 10分以内（3ソース合計）
- **API成功率**: 90%以上（各ソース）
- **重複除去精度**: 85%以上

### 機能指標
- **記事取得数**: 1日15記事（各ソース5記事）
- **検証成功率**: 80%以上
- **要約生成成功率**: 90%以上
- **通知送信成功率**: 95%以上

### 運用指標
- **システム稼働率**: 99%以上
- **エラー発生率**: 5%以下
- **ユーザー満足度**: レビュー評価向上

## 🚨 リスク管理

### 高リスク項目
1. **API制限対応**
   - 軽減策: レート制限監視・複数アカウント運用検討
2. **データフォーマット統一の複雑さ**
   - 軽減策: 共通データクラス・段階的統合テスト

### 中リスク項目
1. **パフォーマンス劣化**
   - 軽減策: 非同期処理・並列処理最適化
2. **運用複雑性増加**
   - 軽減策: 設定検証機能・段階的移行

## 📝 参考情報

### API ドキュメント
- [Reddit API Documentation](https://www.reddit.com/dev/api/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [PRAW (Python Reddit API Wrapper)](https://praw.readthedocs.io/)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)

### 技術参考
- [非同期処理ベストプラクティス](https://docs.python.org/3/library/asyncio.html)
- [API レート制限対応](https://requests.readthedocs.io/en/latest/)

---

**承認者**: 開発チーム  
**次回レビュー**: 実装開始前（Phase 3.1開始前）
