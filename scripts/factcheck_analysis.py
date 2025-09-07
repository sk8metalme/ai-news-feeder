#!/usr/bin/env python3
"""ファクトチェック基準の分析とA/Bテストツール"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.hackernews_api import HackerNewsAPI
from src.api.factcheck_api import FactCheckAPI
from src.utils.config import Config


class FactCheckAnalyzer:
    """ファクトチェック基準の分析ツール"""
    
    def __init__(self):
        self.hn_api = HackerNewsAPI()
        self.fc_api = FactCheckAPI()
        self.results = []
    
    def analyze_threshold_impact(self, hours=24, sample_size=50):
        """異なる閾値での検証結果を分析"""
        print(f"過去{hours}時間のAI記事を分析中...")
        
        # AI関連記事を取得
        stories = self.hn_api.search_ai_stories(hours=hours)[:sample_size]
        
        if not stories:
            print("AI関連記事が見つかりませんでした")
            return
        
        print(f"{len(stories)}件の記事を分析します\n")
        
        # 各記事を検証
        for i, story in enumerate(stories, 1):
            print(f"[{i}/{len(stories)}] {story.get('title')[:60]}...")
            
            # ファクトチェック実行
            verification = self.fc_api.verify_story(story.get('title', ''))
            
            self.results.append({
                'title': story.get('title'),
                'score': story.get('score'),
                'url': story.get('url'),
                'verification': verification
            })
        
        # 結果を分析
        self._analyze_results()
    
    def _analyze_results(self):
        """収集した結果を分析"""
        print("\n" + "="*60)
        print("分析結果")
        print("="*60)
        
        # 基本統計
        total_articles = len(self.results)
        verified_default = sum(1 for r in self.results if r['verification']['verified'])
        
        print(f"\n総記事数: {total_articles}")
        print(f"デフォルト基準での検証済み: {verified_default} ({verified_default/total_articles*100:.1f}%)")
        
        # 信頼度スコアの分布
        scores = [r['verification']['confidence_score'] for r in self.results]
        print(f"\n信頼度スコア分布:")
        print(f"  最小: {min(scores):.3f}")
        print(f"  最大: {max(scores):.3f}")
        print(f"  平均: {sum(scores)/len(scores):.3f}")
        
        # 異なる閾値での結果
        print(f"\n閾値別の検証率:")
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        
        for threshold in thresholds:
            verified = sum(1 for r in self.results 
                         if r['verification']['confidence_score'] >= threshold)
            print(f"  閾値 {threshold:.1f}: {verified} 件 ({verified/total_articles*100:.1f}%)")
        
        # ソース別の統計
        print(f"\nソース別統計:")
        dev_to_articles = sum(1 for r in self.results 
                            if r['verification']['dev_to_count'] > 0)
        medium_articles = sum(1 for r in self.results 
                            if r['verification']['medium_count'] > 0)
        both_sources = sum(1 for r in self.results 
                         if r['verification']['dev_to_count'] > 0 
                         and r['verification']['medium_count'] > 0)
        
        print(f"  dev.toで見つかった: {dev_to_articles} ({dev_to_articles/total_articles*100:.1f}%)")
        print(f"  Mediumで見つかった: {medium_articles} ({medium_articles/total_articles*100:.1f}%)")
        print(f"  両方で見つかった: {both_sources} ({both_sources/total_articles*100:.1f}%)")
        
        # 推奨設定
        print(f"\n推奨設定:")
        recommended_threshold = self._calculate_recommended_threshold()
        print(f"  FACTCHECK_CONFIDENCE_THRESHOLD={recommended_threshold}")
        
        # 詳細レポートを保存
        self._save_detailed_report()
    
    def _calculate_recommended_threshold(self):
        """推奨閾値を計算"""
        # 目標: 全記事の30-50%が検証済みになる閾値
        target_percentage = 0.4  # 40%
        total = len(self.results)
        target_count = int(total * target_percentage)
        
        # スコアをソートして、目標パーセンタイルの値を取得
        scores = sorted([r['verification']['confidence_score'] for r in self.results], 
                       reverse=True)
        
        if target_count < len(scores):
            return round(scores[target_count], 2)
        else:
            return 0.5  # デフォルト
    
    def _save_detailed_report(self):
        """詳細レポートをファイルに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/factcheck_analysis_{timestamp}.json"
        
        os.makedirs('reports', exist_ok=True)
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(self.results),
            'results': self.results,
            'recommended_threshold': self._calculate_recommended_threshold()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n詳細レポートを保存しました: {filename}")
    
    def compare_configurations(self, config_sets):
        """異なる設定での結果を比較（A/Bテスト）"""
        print("A/Bテスト実行中...")
        
        # 記事を取得
        stories = self.hn_api.search_ai_stories(hours=24)[:30]
        
        results_by_config = {}
        
        for config_name, config in config_sets.items():
            print(f"\n設定 '{config_name}' でテスト中...")
            
            # 一時的に設定を変更
            original_values = {}
            for key, value in config.items():
                original_values[key] = getattr(Config, key)
                setattr(Config, key, value)
            
            # 検証実行
            verified_count = 0
            total_confidence = 0
            
            for story in stories:
                verification = self.fc_api.verify_story(story.get('title', ''))
                if verification['verified'] and verification['confidence_score'] >= Config.FACTCHECK_CONFIDENCE_THRESHOLD:
                    verified_count += 1
                total_confidence += verification['confidence_score']
            
            results_by_config[config_name] = {
                'verified_count': verified_count,
                'verification_rate': verified_count / len(stories),
                'avg_confidence': total_confidence / len(stories)
            }
            
            # 設定を元に戻す
            for key, value in original_values.items():
                setattr(Config, key, value)
        
        # 結果を表示
        print("\n" + "="*60)
        print("A/Bテスト結果")
        print("="*60)
        
        for config_name, results in results_by_config.items():
            print(f"\n設定 '{config_name}':")
            print(f"  検証済み記事: {results['verified_count']}/{len(stories)} ({results['verification_rate']*100:.1f}%)")
            print(f"  平均信頼度: {results['avg_confidence']:.3f}")


def main():
    parser = argparse.ArgumentParser(description='ファクトチェック基準の分析ツール')
    parser.add_argument('--analyze', action='store_true', 
                       help='現在の基準での分析を実行')
    parser.add_argument('--ab-test', action='store_true',
                       help='A/Bテストを実行')
    parser.add_argument('--hours', type=int, default=24,
                       help='分析対象の時間範囲（デフォルト: 24時間）')
    parser.add_argument('--sample-size', type=int, default=50,
                       help='分析するサンプル数（デフォルト: 50）')
    
    args = parser.parse_args()
    
    analyzer = FactCheckAnalyzer()
    
    if args.analyze:
        analyzer.analyze_threshold_impact(hours=args.hours, sample_size=args.sample_size)
    
    elif args.ab_test:
        # A/Bテスト設定
        config_sets = {
            '現在の設定': {
                'FACTCHECK_MIN_SOURCES': 1,
                'FACTCHECK_CONFIDENCE_THRESHOLD': 0.5
            },
            '厳格な設定': {
                'FACTCHECK_MIN_SOURCES': 2,
                'FACTCHECK_CONFIDENCE_THRESHOLD': 0.7
            },
            '緩い設定': {
                'FACTCHECK_MIN_SOURCES': 1,
                'FACTCHECK_CONFIDENCE_THRESHOLD': 0.3
            },
            'バランス設定': {
                'FACTCHECK_MIN_SOURCES': 1,
                'FACTCHECK_CONFIDENCE_THRESHOLD': 0.6
            }
        }
        
        analyzer.compare_configurations(config_sets)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()