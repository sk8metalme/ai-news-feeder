"""
Report generation utilities for AI News Feeder
"""
import json
import os
from datetime import datetime
from typing import List, Dict
from .logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Class for generating structured reports"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def generate_json_report(self, verification_results: List[Dict]) -> str:
        """Generate a JSON report from verification results"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_articles": len(verification_results),
            "verified_articles": len([r for r in verification_results if r.get('verification_status') == 'verified']),
            "verification_results": verification_results
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def save_daily_report(self, verification_results: List[Dict]) -> str:
        """Save daily report to file"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"ai_news_report_{date_str}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        report_content = self.generate_json_report(verification_results)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Daily report saved to {filepath}")
            return filepath
            
        except IOError as e:
            logger.error(f"Failed to save daily report: {e}")
            return ""
    
    def generate_summary_stats(self, verification_results: List[Dict]) -> Dict:
        """Generate summary statistics from verification results"""
        if not verification_results:
            return {
                "total_articles": 0,
                "verified_articles": 0,
                "verification_rate": 0.0,
                "sources_breakdown": {"dev_to": 0, "medium": 0}
            }
        
        verified_count = 0
        dev_to_total = 0
        medium_total = 0
        
        for result in verification_results:
            if result.get('verification_status') == 'verified':
                verified_count += 1
            
            related_articles = result.get('related_articles', {})
            dev_to_total += len(related_articles.get('dev_to', []))
            medium_total += len(related_articles.get('medium', []))
        
        total_articles = len(verification_results)
        verification_rate = (verified_count / total_articles * 100) if total_articles > 0 else 0
        
        return {
            "total_articles": total_articles,
            "verified_articles": verified_count,
            "verification_rate": round(verification_rate, 2),
            "sources_breakdown": {
                "dev_to": dev_to_total,
                "medium": medium_total
            }
        }
