#!/usr/bin/env python3
"""接続テストスクリプト"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.hackernews_api import HackerNewsAPI
from src.utils.config import Config
import logging

logging.basicConfig(level=logging.INFO)

def test_hackernews_connection():
    """Hacker News API接続テスト"""
    print("🔍 Hacker News API接続テスト...")
    api = HackerNewsAPI()
    
    # トップストーリーを取得
    story_ids = api.get_top_stories(limit=5)
    if story_ids:
        print(f"✅ 接続成功！ {len(story_ids)}件のストーリーIDを取得")
        
        # 最初のストーリーの詳細を取得
        story = api.get_story(story_ids[0])
        if story:
            print(f"📰 サンプル記事: {story.get('title')}")
            print(f"   スコア: {story.get('score')}")
            print(f"   URL: {story.get('url')}")
    else:
        print("❌ 接続失敗")

def test_ai_search():
    """AI記事検索テスト"""
    print("\n🤖 AI記事検索テスト...")
    api = HackerNewsAPI()
    
    stories = api.search_ai_stories(hours=48)  # 過去48時間で検索
    if stories:
        print(f"✅ {len(stories)}件のAI関連記事を発見！")
        for i, story in enumerate(stories[:3], 1):
            print(f"\n{i}. {story.get('title')}")
            print(f"   スコア: {story.get('score')}")
    else:
        print("❌ AI関連記事が見つかりませんでした")

def test_config():
    """設定確認"""
    print("\n⚙️  設定確認...")
    print(f"記事数/日: {Config.ARTICLES_PER_DAY}")
    print(f"最低スコア: {Config.MINIMUM_SCORE}")
    print(f"AIキーワード: {', '.join(Config.AI_KEYWORDS[:5])}...")
    
    if Config.SLACK_WEBHOOK_URL:
        print("✅ Slack Webhook URL設定済み")
    else:
        print("⚠️  Slack Webhook URLが未設定です")

if __name__ == "__main__":
    print("AI News Feeder 接続テスト")
    print("=" * 50)
    
    test_config()
    test_hackernews_connection()
    test_ai_search()
    
    print("\n" + "=" * 50)
    print("テスト完了！")