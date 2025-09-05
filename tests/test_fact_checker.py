"""
Tests for fact checker module
"""
import pytest
import responses
from unittest.mock import Mock, patch

from src.verification.fact_checker import FactChecker


class TestFactChecker:
    """Test cases for FactChecker class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.fact_checker = FactChecker()
    
    @responses.activate
    def test_search_dev_to_success(self):
        """Test successful dev.to search"""
        mock_articles = [
            {
                "title": "Understanding ChatGPT and AI",
                "url": "https://dev.to/article1",
                "description": "A deep dive into ChatGPT technology",
                "tag_list": ["ai", "chatgpt"],
                "published_at": "2022-01-01T00:00:00Z"
            },
            {
                "title": "Web Development Tips",
                "url": "https://dev.to/article2", 
                "description": "Tips for better web development",
                "tag_list": ["javascript", "web"],
                "published_at": "2022-01-01T00:00:00Z"
            }
        ]
        
        responses.add(
            responses.GET,
            "https://dev.to/api/articles",
            json=mock_articles,
            status=200
        )
        
        result = self.fact_checker.search_dev_to("ChatGPT AI model")
        
        # Should find the AI-related article
        assert len(result) == 1
        assert result[0]["title"] == "Understanding ChatGPT and AI"
        assert result[0]["source"] == "dev.to"
    
    @responses.activate
    def test_search_dev_to_no_matches(self):
        """Test dev.to search with no matches"""
        mock_articles = [
            {
                "title": "Web Development Tips",
                "url": "https://dev.to/article1",
                "description": "Tips for better web development",
                "tag_list": ["javascript", "web"],
                "published_at": "2022-01-01T00:00:00Z"
            }
        ]
        
        responses.add(
            responses.GET,
            "https://dev.to/api/articles",
            json=mock_articles,
            status=200
        )
        
        result = self.fact_checker.search_dev_to("ChatGPT AI model")
        
        # Should find no matches
        assert len(result) == 0
    
    @responses.activate
    def test_search_dev_to_api_error(self):
        """Test dev.to search API error handling"""
        responses.add(
            responses.GET,
            "https://dev.to/api/articles",
            status=500
        )
        
        result = self.fact_checker.search_dev_to("ChatGPT AI model")
        assert result == []
    
    @responses.activate
    def test_search_medium_success(self):
        """Test successful Medium search"""
        rss_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Advanced ChatGPT Techniques</title>
                    <link>https://medium.com/article1</link>
                    <pubDate>Sat, 01 Jan 2022 00:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Web Design Principles</title>
                    <link>https://medium.com/article2</link>
                    <pubDate>Sat, 01 Jan 2022 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>'''
        
        # Mock RSS responses for different tags
        tags = ['artificial-intelligence', 'ai', 'machine-learning', 'chatgpt']
        for tag in tags:
            responses.add(
                responses.GET,
                f"https://medium.com/feed/tag/{tag}",
                body=rss_content,
                status=200,
                content_type='application/xml'
            )
        
        with patch('time.sleep'):  # Mock sleep to speed up tests
            result = self.fact_checker.search_medium("ChatGPT techniques")
        
        # Should find the ChatGPT-related article (from each tag, so multiple)
        assert len(result) > 0
        assert any("ChatGPT" in article["title"] for article in result)
        assert all(article["source"] == "medium" for article in result)
    
    @responses.activate
    def test_search_medium_api_error(self):
        """Test Medium search with API errors"""
        # Mock failed responses for all tags
        tags = ['artificial-intelligence', 'ai', 'machine-learning', 'chatgpt']
        for tag in tags:
            responses.add(
                responses.GET,
                f"https://medium.com/feed/tag/{tag}",
                status=500
            )
        
        with patch('time.sleep'):
            result = self.fact_checker.search_medium("ChatGPT techniques")
        
        assert result == []
    
    def test_extract_search_terms(self):
        """Test search term extraction"""
        test_cases = [
            ("New ChatGPT-4 AI Model Released by OpenAI", "chatgpt-4 model released openai"),
            ("The Future of Machine Learning", "future machine learning"),
            ("A Brief Guide to AI", "brief guide"),
            ("Understanding Neural Networks in 2023", "understanding neural networks 2023"),
        ]
        
        for title, expected in test_cases:
            result = self.fact_checker._extract_search_terms(title)
            # Check that key terms are present
            for expected_term in expected.split():
                if len(expected_term) > 3:  # Only check meaningful terms
                    assert expected_term.lower() in result.lower()
    
    @patch.object(FactChecker, 'search_dev_to')
    @patch.object(FactChecker, 'search_medium')
    def test_verify_article_verified(self, mock_medium, mock_dev_to):
        """Test article verification - verified case"""
        # Mock search results
        mock_dev_to.return_value = [
            {"title": "Related article", "url": "https://dev.to/article1", "source": "dev.to"}
        ]
        mock_medium.return_value = [
            {"title": "Another related article", "url": "https://medium.com/article1", "source": "medium"}
        ]
        
        result = self.fact_checker.verify_article(
            "ChatGPT-4 Released", 
            "https://example.com/chatgpt4"
        )
        
        assert result["verification_status"] == "verified"
        assert result["total_related_count"] == 2
        assert len(result["related_articles"]["dev_to"]) == 1
        assert len(result["related_articles"]["medium"]) == 1
        assert result["article_title"] == "ChatGPT-4 Released"
        assert result["article_url"] == "https://example.com/chatgpt4"
    
    @patch.object(FactChecker, 'search_dev_to')
    @patch.object(FactChecker, 'search_medium')
    def test_verify_article_unverified(self, mock_medium, mock_dev_to):
        """Test article verification - unverified case"""
        # Mock no search results
        mock_dev_to.return_value = []
        mock_medium.return_value = []
        
        result = self.fact_checker.verify_article(
            "Unknown AI News", 
            "https://example.com/unknown"
        )
        
        assert result["verification_status"] == "unverified"
        assert result["total_related_count"] == 0
        assert len(result["related_articles"]["dev_to"]) == 0
        assert len(result["related_articles"]["medium"]) == 0
