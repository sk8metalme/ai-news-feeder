"""
Article summarizer using Claude CLI
"""
import subprocess
import requests
from typing import Dict, Optional
import tempfile
import os
from bs4 import BeautifulSoup
from .logger import get_logger

logger = get_logger(__name__)


class ArticleSummarizer:
    """Class for summarizing articles using Claude CLI"""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
        self._check_claude_cli_availability()
    
    def _check_claude_cli_availability(self) -> bool:
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(
                [self.claude_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Claude CLI available: {result.stdout.strip()}")
                return True
            else:
                logger.warning("Claude CLI not available or not configured")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Claude CLI check failed: {e}")
            return False
    
    def _fetch_article_content(self, url: str) -> Optional[str]:
        """Fetch and extract article content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML and extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content areas
            content_selectors = [
                'article', '.article-content', '.post-content', 
                '.content', '.entry-content', 'main', '.main-content'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    break
            
            # Fallback to body content
            if not content:
                content = soup.body.get_text(strip=True) if soup.body else soup.get_text(strip=True)
            
            # Clean up the content
            lines = (line.strip() for line in content.splitlines())
            content = '\\n'.join(line for line in lines if len(line) > 10)  # Filter out short lines
            
            if len(content) < 100:
                logger.warning(f"Extracted content too short ({len(content)} chars): {url}")
                return None
            
            logger.info(f"Successfully extracted {len(content)} characters from {url}")
            return content[:8000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Failed to fetch article content from {url}: {e}")
            return None
    
    def _create_summary_prompt(self, title: str, content: str) -> str:
        """Create a prompt for Claude to summarize the article"""
        prompt = f"""以下のAI関連記事を日本語で要約してください。

記事タイトル: {title}

記事内容:
{content}

要約の要件:
1. 3-4文で簡潔にまとめる
2. 技術的なポイントを含める
3. なぜ重要なのかを説明する
4. 日本語で出力する
5. 専門用語は適度に説明を加える

要約:"""
        return prompt
    
    def _call_claude_cli(self, prompt: str) -> Optional[str]:
        """Call Claude CLI with the given prompt"""
        try:
            # Create temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(prompt)
                prompt_file = f.name
            
            try:
                # Call Claude CLI
                result = subprocess.run(
                    [self.claude_cli_path, "chat", "--file", prompt_file],
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
                
                if result.returncode == 0:
                    summary = result.stdout.strip()
                    logger.info(f"Claude CLI summary generated: {len(summary)} characters")
                    return summary
                else:
                    logger.error(f"Claude CLI failed: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(prompt_file)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            logger.error("Claude CLI call timed out")
            return None
        except Exception as e:
            logger.error(f"Claude CLI call failed: {e}")
            return None
    
    def summarize_article(self, title: str, url: str) -> Dict[str, str]:
        """Summarize an article using Claude CLI"""
        logger.info(f"Summarizing article: {title}")
        
        result = {
            'title': title,
            'url': url,
            'summary': None,
            'summary_status': 'failed',
            'error': None
        }
        
        # Check if Claude CLI is available
        if not self._check_claude_cli_availability():
            result['error'] = 'Claude CLI not available'
            result['summary'] = '要約機能は現在利用できません（Claude CLI未設定）'
            return result
        
        # Fetch article content
        content = self._fetch_article_content(url)
        if not content:
            result['error'] = 'Failed to fetch article content'
            result['summary'] = '記事の内容を取得できませんでした'
            return result
        
        # Create prompt and call Claude
        prompt = self._create_summary_prompt(title, content)
        summary = self._call_claude_cli(prompt)
        
        if summary:
            result['summary'] = summary
            result['summary_status'] = 'success'
            logger.info(f"Article summarization completed: {title}")
        else:
            result['error'] = 'Claude CLI summarization failed'
            result['summary'] = '要約の生成に失敗しました'
        
        return result
    
    def is_available(self) -> bool:
        """Check if the summarizer is available for use"""
        return self._check_claude_cli_availability()
