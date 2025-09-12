#!/usr/bin/env python3
"""Fact-check analysis tool (v2, uses new FactChecker)"""
import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.hacker_news import HackerNewsAPI
from src.verification.fact_checker import FactChecker
from config import settings


def analyze(hours=24, sample_size=50):
    hn = HackerNewsAPI()
    fc = FactChecker(enable_summarization=settings.ENABLE_SUMMARIZATION)

    stories = hn.get_ai_stories(max_stories=200, hours=hours)[:sample_size]
    if not stories:
        print("AI関連記事が見つかりませんでした")
        return 1

    results = []
    for i, s in enumerate(stories, 1):
        print(f"[{i}/{len(stories)}] {s.get('title','')[:60]}...")
        r = fc.verify_article(s.get('title',''), s.get('url',''))
        results.append(r)

    # 集計
    total = len(results)
    verified = sum(1 for r in results if r.get('verification_status') == 'verified')
    partial = sum(1 for r in results if r.get('verification_status') == 'partially_verified')
    dev_hits = sum(len(r.get('related_articles',{}).get('dev_to',[])) for r in results)
    med_hits = sum(len(r.get('related_articles',{}).get('medium',[])) for r in results)

    print("\n=== 分析結果 (v2) ===")
    print(f"総記事数: {total}")
    print(f"✅ Verified: {verified} ({verified/total*100:.1f}%)")
    print(f"🟡 Partially: {partial} ({partial/total*100:.1f}%)")
    print(f"dev.to関連記事: {dev_hits} / Medium関連記事: {med_hits}")

    # レポート保存
    os.makedirs('reports', exist_ok=True)
    fname = f"reports/factcheck_analysis_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'hours': hours,
            'sample_size': sample_size,
            'summary': {
                'total': total,
                'verified': verified,
                'partially_verified': partial,
                'dev_to_total': dev_hits,
                'medium_total': med_hits
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n詳細レポートを保存しました: {fname}")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Fact-check analysis (v2)')
    parser.add_argument('--hours', type=int, default=24)
    parser.add_argument('--sample-size', type=int, default=50)
    args = parser.parse_args()
    sys.exit(analyze(hours=args.hours, sample_size=args.sample_size))


if __name__ == '__main__':
    main()

