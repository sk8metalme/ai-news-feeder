#!/bin/bash
# AI News Feeder セットアップスクリプト

echo "🚀 AI News Feeder セットアップを開始します..."

# 1. 仮想環境の作成
echo "📦 仮想環境を作成中..."
python3 -m venv venv
source venv/bin/activate

# 2. 依存関係のインストール
echo "📚 依存関係をインストール中..."
pip install -r requirements.txt

# 3. 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "🔧 環境変数ファイルを作成中..."
    cp .env.example .env
    echo ""
    echo "⚠️  .envファイルを編集してSLACK_WEBHOOK_URLを設定してください"
    echo ""
fi

# 4. ディレクトリの作成
echo "📁 必要なディレクトリを作成中..."
mkdir -p reports logs

# 5. テスト実行の提案
echo ""
echo "✅ セットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "1. .envファイルを編集してSLACK_WEBHOOK_URLを設定"
echo "2. テスト実行: python main.py"
echo "3. cron設定: ./scripts/setup_cron.sh"
echo ""