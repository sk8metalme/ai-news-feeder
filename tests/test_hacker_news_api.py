"""
Tests for Hacker News API module
"""
import pytest
import responses
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.api.hacker_news import HackerNewsAPI


class TestHackerNewsAPI:
    """Test cases for HackerNewsAPI class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.api = HackerNewsAPI()
    
    @responses.activate
    def test_get_top_stories_success(self):
        """Test successful retrieval of top stories"""
        # Mock response
        story_ids = [1, 2, 3, 4, 5]
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            json=story_ids,
            status=200
        )
        
        result = self.api.get_top_stories()
        assert result == story_ids
    
    @responses.activate
    def test_get_top_stories_failure(self):
        """Test handling of API failure"""
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            status=500
        )
        
        result = self.api.get_top_stories()
        assert result == []
    
    @responses.activate
    def test_get_story_details_success(self, sample_hn_story):
        """Test successful retrieval of story details"""
        story_id = 12345
        responses.add(
            responses.GET,
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
            json=sample_hn_story,
            status=200
        )
        
        result = self.api.get_story_details(story_id)
        assert result == sample_hn_story
    
    @responses.activate
    def test_get_story_details_failure(self):
        """Test handling of story details API failure"""
        story_id = 12345
        responses.add(
            responses.GET,
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
            status=404
        )
        
        result = self.api.get_story_details(story_id)
        assert result is None
    
    def test_is_ai_related_positive(self):
        """Test AI-related story detection - positive cases"""
        ai_stories = [
            {"title": "ChatGPT-4 releases new features", "text": "", "url": ""},
            {"title": "Machine learning breakthrough", "text": "", "url": ""},
            {"title": "OpenAI announces new model", "text": "", "url": ""},
            {"title": "Regular title", "text": "Article about artificial intelligence", "url": ""},
            {"title": "Regular title", "text": "", "url": "https://example.com/gpt-news"},
        ]
        
        for story in ai_stories:
            assert self.api.is_ai_related(story), f"Should detect AI content in: {story}"
    
    def test_is_ai_related_negative(self):
        """Test AI-related story detection - negative cases"""
        non_ai_stories = [
            {"title": "Stock market update", "text": "", "url": ""},
            {"title": "New programming language", "text": "Python features", "url": ""},
            {"title": "Weather forecast", "text": "", "url": "https://weather.com"},
        ]
        
        for story in non_ai_stories:
            assert not self.api.is_ai_related(story), f"Should not detect AI content in: {story}"
    
    def test_is_recent_positive(self):
        """Test recent story detection - positive cases"""
        now = datetime.now()
        recent_time = int((now - timedelta(hours=12)).timestamp())
        
        story = {"time": recent_time}
        assert self.api.is_recent(story, hours=24)
    
    def test_is_recent_negative(self):
        """Test recent story detection - negative cases"""
        now = datetime.now()
        old_time = int((now - timedelta(hours=48)).timestamp())
        
        story = {"time": old_time}
        assert not self.api.is_recent(story, hours=24)
    
    def test_is_recent_no_time(self):
        """Test recent story detection with missing time"""
        story = {}
        assert not self.api.is_recent(story)
    
    @responses.activate
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_get_ai_stories_integration(self, mock_sleep, sample_hn_story):
        """Test complete AI stories retrieval workflow"""
        # Mock top stories API
        story_ids = [1, 2, 3]
        responses.add(
            responses.GET,
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            json=story_ids,
            status=200
        )
        
        # Mock individual story APIs
        for story_id in story_ids:
            story_data = sample_hn_story.copy()
            story_data["id"] = story_id
            if story_id == 1:
                # First story is AI-related and recent
                story_data["title"] = "ChatGPT breakthrough in AI"
                story_data["score"] = 100
                story_data["time"] = int(datetime.now().timestamp())
            else:
                # Other stories are not AI-related or low score
                story_data["title"] = "Non-AI related news"
                story_data["score"] = 10
            
            responses.add(
                responses.GET,
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                json=story_data,
                status=200
            )
        
        result = self.api.get_ai_stories(max_stories=10, hours=24)
        
        # Should only return the AI-related story with sufficient score
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert "ChatGPT" in result[0]["title"]
