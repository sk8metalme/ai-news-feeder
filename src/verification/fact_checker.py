"""
Fact checking module for verifying news articles
"""
import requests
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import quote
from ..utils.logger import get_logger
from config.settings import DEV_TO_API_URL, MEDIUM_RSS_URL

logger = get_logger(__name__)


class FactChecker:
    """Class for fact-checking news articles against external sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search_dev_to(self, query: str) -> List[Dict]:
        """Search for related articles on dev.to"""
        try:
            params = {
                'tag': 'ai,machinelearning,chatgpt,openai',
                'per_page': 5,
                'top': 7  # Articles from last week
            }
            
            response = self.session.get(DEV_TO_API_URL, params=params, timeout=10)
            response.raise_for_status()
            
            articles = response.json()
            related_articles = []
            
            # Simple keyword matching
            query_words = set(query.lower().split())
            
            for article in articles:
                title = article.get('title', '').lower()
                description = article.get('description', '').lower()
                tags = ' '.join(article.get('tag_list', [])).lower()
                
                content = f"{title} {description} {tags}"
                
                # Check if query words are in the article content
                if any(word in content for word in query_words if len(word) > 3):
                    related_articles.append({
                        'title': article.get('title'),
                        'url': article.get('url'),
                        'source': 'dev.to',
                        'published_at': article.get('published_at')
                    })
            
            return related_articles
            
        except requests.RequestException as e:
            logger.error(f"Failed to search dev.to: {e}")
            return []
    
    def search_medium(self, query: str) -> List[Dict]:
        """Search for related articles on Medium (simplified approach)"""
        try:
            # Use Medium's tag-based RSS feed for AI-related content
            tags = ['artificial-intelligence', 'ai', 'machine-learning', 'chatgpt']
            related_articles = []
            
            for tag in tags:
                try:
                    rss_url = MEDIUM_RSS_URL.format(tag=tag)
                    response = self.session.get(rss_url, timeout=10)
                    response.raise_for_status()
                    
                    # Parse XML using built-in xml.etree.ElementTree
                    try:
                        root = ET.fromstring(response.content)
                        items = root.findall('.//item')[:3]  # Limit to 3 per tag
                        
                        query_words = set(query.lower().split())
                        
                        for item in items:
                            title_elem = item.find('title')
                            title_text = title_elem.text if title_elem is not None else ''
                            
                            # Simple keyword matching
                            if any(word in title_text.lower() for word in query_words if len(word) > 3):
                                link_elem = item.find('link')
                                pub_date_elem = item.find('pubDate')
                                
                                related_articles.append({
                                    'title': title_text,
                                    'url': link_elem.text if link_elem is not None else '',
                                    'source': 'medium',
                                    'published_at': pub_date_elem.text if pub_date_elem is not None else ''
                                })
                    except ET.ParseError as parse_error:
                        logger.warning(f"Failed to parse XML for tag {tag}: {parse_error}")
                        continue
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Failed to search Medium tag {tag}: {e}")
                    continue
            
            return related_articles
            
        except Exception as e:
            logger.error(f"Failed to search Medium: {e}")
            return []
    
    def verify_article(self, title: str, url: str) -> Dict:
        """Verify an article by searching for related content"""
        logger.info(f"Verifying article: {title}")
        
        # Extract key terms from title for search
        search_query = self._extract_search_terms(title)
        
        # Search external sources
        dev_to_articles = self.search_dev_to(search_query)
        medium_articles = self.search_medium(search_query)
        
        # Calculate verification score
        total_related = len(dev_to_articles) + len(medium_articles)
        verification_status = "verified" if total_related >= 1 else "unverified"
        
        result = {
            'article_title': title,
            'article_url': url,
            'verification_status': verification_status,
            'related_articles': {
                'dev_to': dev_to_articles,
                'medium': medium_articles
            },
            'total_related_count': total_related,
            'checked_at': time.strftime('%Y-%m-%d %H:%M:%S JST')
        }
        
        logger.info(f"Verification result: {verification_status} ({total_related} related articles)")
        return result
    
    def _extract_search_terms(self, title: str) -> str:
        """Extract key search terms from article title"""
        # Remove common words and focus on meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        words = [word.strip('.,!?;:()[]"\'') for word in title.lower().split()]
        key_words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return ' '.join(key_words[:5])  # Limit to top 5 terms
