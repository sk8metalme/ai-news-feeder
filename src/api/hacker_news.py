"""
Hacker News API client for fetching AI-related articles
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from ..utils.logger import get_logger
from config.settings import HACKER_NEWS_API_URL, AI_KEYWORDS, SCORE_THRESHOLD

logger = get_logger(__name__)


class HackerNewsAPI:
    """Client for interacting with Hacker News API"""
    
    def __init__(self):
        self.base_url = HACKER_NEWS_API_URL
        
    def get_top_stories(self) -> List[int]:
        """Fetch top story IDs from Hacker News"""
        try:
            response = requests.get(f"{self.base_url}/topstories.json", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch top stories: {e}")
            return []
    
    def get_story_details(self, story_id: int) -> Optional[Dict]:
        """Fetch details for a specific story"""
        try:
            response = requests.get(f"{self.base_url}/item/{story_id}.json", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch story {story_id}: {e}")
            return None
    
    def is_ai_related(self, story: Dict) -> bool:
        """Check if a story is AI-related based on keywords"""
        title = story.get("title", "").lower()
        text = story.get("text", "").lower()
        url = story.get("url", "").lower()
        
        content = f"{title} {text} {url}"
        
        return any(keyword.lower() in content for keyword in AI_KEYWORDS)
    
    def is_recent(self, story: Dict, hours: int = 24) -> bool:
        """Check if a story was posted within the last N hours"""
        story_time = story.get("time")
        if not story_time:
            return False
        
        story_datetime = datetime.fromtimestamp(story_time)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return story_datetime >= cutoff_time
    
    def get_ai_stories(self, max_stories: int = 100, hours: int = 24) -> List[Dict]:
        """Fetch recent AI-related stories with sufficient score"""
        logger.info(f"Fetching AI stories from last {hours} hours")
        
        top_story_ids = self.get_top_stories()[:max_stories]
        ai_stories = []
        
        for story_id in top_story_ids:
            # Add delay to respect rate limits
            time.sleep(0.1)
            
            story = self.get_story_details(story_id)
            if not story:
                continue
            
            # Filter by criteria
            if (story.get("score", 0) >= SCORE_THRESHOLD and 
                self.is_ai_related(story) and 
                self.is_recent(story, hours)):
                
                ai_stories.append(story)
                logger.info(f"Found AI story: {story.get('title', 'No title')}")
        
        logger.info(f"Found {len(ai_stories)} AI stories")
        return ai_stories
