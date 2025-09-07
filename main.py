#!/usr/bin/env python3
"""AI News Feeder - メインエントリーポイント"""
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.processing.news_processor import run_daily_process


if __name__ == "__main__":
    print("AI News Feeder を実行しています...")
    success = run_daily_process()
    
    if success:
        print("処理が正常に完了しました")
        sys.exit(0)
    else:
        print("処理中にエラーが発生しました")
        sys.exit(1)