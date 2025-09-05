"""
Tests for report generator module
"""
import pytest
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch

from src.utils.report_generator import ReportGenerator


class TestReportGenerator:
    """Test cases for ReportGenerator class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.report_generator = ReportGenerator(data_dir="test_data")
    
    def test_generate_json_report(self, sample_verification_result):
        """Test JSON report generation"""
        verification_results = [
            sample_verification_result,
            {
                **sample_verification_result,
                "verification_status": "unverified",
                "total_related_count": 0
            }
        ]
        
        report_json = self.report_generator.generate_json_report(verification_results)
        report_data = json.loads(report_json)
        
        assert "generated_at" in report_data
        assert report_data["total_articles"] == 2
        assert report_data["verified_articles"] == 1
        assert len(report_data["verification_results"]) == 2
        assert report_data["verification_results"][0] == sample_verification_result
    
    def test_generate_json_report_empty(self):
        """Test JSON report generation with empty results"""
        report_json = self.report_generator.generate_json_report([])
        report_data = json.loads(report_json)
        
        assert report_data["total_articles"] == 0
        assert report_data["verified_articles"] == 0
        assert report_data["verification_results"] == []
    
    @patch('os.makedirs')
    def test_save_daily_report(self, mock_makedirs, sample_verification_result, temp_data_dir):
        """Test saving daily report to file"""
        # Use temporary directory
        report_generator = ReportGenerator(data_dir=temp_data_dir)
        verification_results = [sample_verification_result]
        
        filepath = report_generator.save_daily_report(verification_results)
        
        # Check that file was created
        assert os.path.exists(filepath)
        
        # Check file content
        with open(filepath, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        assert report_data["total_articles"] == 1
        assert report_data["verified_articles"] == 1
        
        # Check filename format
        date_str = datetime.now().strftime('%Y%m%d')
        expected_filename = f"ai_news_report_{date_str}.json"
        assert expected_filename in filepath
    
    @patch('builtins.open', side_effect=IOError("File write error"))
    def test_save_daily_report_failure(self, mock_open, sample_verification_result):
        """Test handling of file save failure"""
        verification_results = [sample_verification_result]
        
        filepath = self.report_generator.save_daily_report(verification_results)
        
        # Should return empty string on failure
        assert filepath == ""
    
    def test_generate_summary_stats(self, sample_verification_result):
        """Test summary statistics generation"""
        verification_results = [
            sample_verification_result,  # verified with 2 total (1 dev.to, 1 medium)
            {
                **sample_verification_result,
                "verification_status": "unverified",
                "total_related_count": 0,
                "related_articles": {"dev_to": [], "medium": []}
            },
            {
                **sample_verification_result,
                "verification_status": "verified",
                "total_related_count": 3,
                "related_articles": {
                    "dev_to": [{"title": "Article 1"}, {"title": "Article 2"}],
                    "medium": [{"title": "Article 3"}]
                }
            }
        ]
        
        stats = self.report_generator.generate_summary_stats(verification_results)
        
        assert stats["total_articles"] == 3
        assert stats["verified_articles"] == 2
        assert stats["verification_rate"] == 66.67  # 2/3 * 100, rounded
        assert stats["sources_breakdown"]["dev_to"] == 3  # 1 + 0 + 2
        assert stats["sources_breakdown"]["medium"] == 2  # 1 + 0 + 1
    
    def test_generate_summary_stats_empty(self):
        """Test summary statistics with empty results"""
        stats = self.report_generator.generate_summary_stats([])
        
        assert stats["total_articles"] == 0
        assert stats["verified_articles"] == 0
        assert stats["verification_rate"] == 0.0
        assert stats["sources_breakdown"]["dev_to"] == 0
        assert stats["sources_breakdown"]["medium"] == 0
