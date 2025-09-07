# ファクトチェック基準の調整ガイド

## 概要
AI News Feederのファクトチェック機能は、環境変数を通じて柔軟に調整可能です。このガイドでは、最適な設定を見つけるための方法を説明します。

## 🎯 調整可能なパラメータ

### 1. FACTCHECK_MIN_SOURCES（デフォルト: 1）
- **説明**: 記事を「検証済み」と判定するために必要な最低関連記事数
- **推奨値**: 
  - 緩い基準: 1
  - 標準: 2-3
  - 厳格: 5以上

### 2. FACTCHECK_MIN_DEV_TO（デフォルト: 0）
- **説明**: dev.toで必要な最低記事数
- **用途**: dev.toの技術記事を重視する場合に設定

### 3. FACTCHECK_MIN_MEDIUM（デフォルト: 0）
- **説明**: Mediumで必要な最低記事数
- **用途**: Mediumの解説記事を重視する場合に設定

### 4. FACTCHECK_CONFIDENCE_THRESHOLD（デフォルト: 0.5）
- **説明**: 信頼度スコアの閾値（0.0-1.0）
- **推奨値**:
  - 緩い基準: 0.3-0.4
  - 標準: 0.5-0.6
  - 厳格: 0.7-0.8

## 📊 信頼度スコアの仕組み

信頼度スコアは以下の要素から計算されます：

1. **基本スコア（70%）**: 関連記事の総数
   - 10記事で最大スコア（1.0）

2. **重み付けスコア（30%）**: ソース別の重み
   - dev.to: 60%
   - Medium: 40%

3. **多様性ボーナス（+0.2）**: 両方のソースから記事が見つかった場合

## 🔧 分析ツールの使用方法

### 1. 現在の設定を分析
```bash
python scripts/factcheck_analysis.py --analyze
```

このコマンドで以下が確認できます：
- 現在の設定での検証率
- 信頼度スコアの分布
- 推奨閾値

### 2. A/Bテストの実行
```bash
python scripts/factcheck_analysis.py --ab-test
```

異なる設定での結果を比較できます。

### 3. カスタム分析
```bash
# 過去48時間、100記事を分析
python scripts/factcheck_analysis.py --analyze --hours 48 --sample-size 100
```

## 📈 推奨調整プロセス

### Step 1: ベースライン測定
1. デフォルト設定で1週間運用
2. 分析ツールで結果を確認
3. 問題点を特定

### Step 2: 段階的調整
1. **検証率が低すぎる場合**（20%未満）
   ```env
   FACTCHECK_MIN_SOURCES=1
   FACTCHECK_CONFIDENCE_THRESHOLD=0.3
   ```

2. **誤検知が多い場合**
   ```env
   FACTCHECK_MIN_SOURCES=2
   FACTCHECK_CONFIDENCE_THRESHOLD=0.6
   ```

3. **バランス重視**
   ```env
   FACTCHECK_MIN_SOURCES=1
   FACTCHECK_CONFIDENCE_THRESHOLD=0.5
   FACTCHECK_MIN_DEV_TO=1  # dev.toで最低1記事必須
   ```

### Step 3: 効果測定
- 1週間ごとに結果を分析
- 必要に応じて微調整
- 最適値が見つかったら固定

## 🎯 ユースケース別推奨設定

### 1. 速報重視（多くの記事を配信）
```env
FACTCHECK_MIN_SOURCES=1
FACTCHECK_CONFIDENCE_THRESHOLD=0.3
```

### 2. 信頼性重視（確実な記事のみ）
```env
FACTCHECK_MIN_SOURCES=3
FACTCHECK_CONFIDENCE_THRESHOLD=0.7
FACTCHECK_MIN_DEV_TO=1
FACTCHECK_MIN_MEDIUM=1
```

### 3. バランス型（標準的な運用）
```env
FACTCHECK_MIN_SOURCES=2
FACTCHECK_CONFIDENCE_THRESHOLD=0.5
```

## 📊 実際の運用例

### 例1: スタートアップのSlack
- **目的**: AI業界の最新動向を幅広くキャッチ
- **設定**: 緩い基準で多めの記事を配信
- **結果**: 1日10-15記事、検証率60%

### 例2: 研究機関のチャンネル
- **目的**: 信頼できる情報のみを共有
- **設定**: 厳格な基準で精選
- **結果**: 1日2-3記事、検証率15%

## ⚠️ 注意事項

1. **段階的な変更**: 急激な変更は避け、段階的に調整
2. **定期的な見直し**: AI記事のトレンドは変化するため、月1回は設定を見直す
3. **フィードバック収集**: Slackでの反応を確認し、調整に反映

## 🔍 トラブルシューティング

### 記事が少なすぎる
1. `FACTCHECK_CONFIDENCE_THRESHOLD`を0.1ずつ下げる
2. `FACTCHECK_MIN_SOURCES`を1に設定
3. AIキーワードを追加（config.py）

### 質の低い記事が多い
1. `FACTCHECK_CONFIDENCE_THRESHOLD`を0.1ずつ上げる
2. `FACTCHECK_MIN_DEV_TO`または`FACTCHECK_MIN_MEDIUM`を1以上に設定
3. `MINIMUM_SCORE`（Hacker Newsスコア）を上げる

---

**最終更新**: 2025-09-06
**関連ドキュメント**: README.md, CHANGELOG.md