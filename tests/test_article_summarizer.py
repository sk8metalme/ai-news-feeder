"""
Tests for article summarizer module
"""
import pytest
import responses
from unittest.mock import Mock, patch, mock_open
import subprocess
import tempfile
import os

from src.utils.article_summarizer import ArticleSummarizer


class TestArticleSummarizer:
    """Test cases for ArticleSummarizer class"""
    
    def setup_method(self):
        """Setup test instance"""
        self.summarizer = ArticleSummarizer()
    
    @patch('subprocess.run')
    def test_check_claude_cli_availability_success(self, mock_run):
        """Test successful Claude CLI availability check"""
        mock_run.return_value = Mock(returncode=0, stdout="Claude CLI v1.0.0")
        
        result = self.summarizer._check_claude_cli_availability()
        
        assert result is True
        mock_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_check_claude_cli_availability_failure(self, mock_run):
        """Test Claude CLI availability check failure"""
        mock_run.side_effect = FileNotFoundError("claude not found")
        
        result = self.summarizer._check_claude_cli_availability()
        
        assert result is False
    
    @responses.activate
    def test_fetch_article_content_success(self):
        """Test successful article content fetching"""
        test_url = "https://example.com/article"
        html_content = """
        <html>
            <body>
                <article>
                    <h1>Test Article Title</h1>
                    <p>This is a test article about AI and machine learning.</p>
                    <p>It contains multiple paragraphs with meaningful content.</p>
                    <p>The content should be long enough to pass the length check.</p>
                </article>
            </body>
        </html>
        """
        
        responses.add(
            responses.GET,
            test_url,
            body=html_content,
            status=200,
            content_type='text/html'
        )
        
        result = self.summarizer._fetch_article_content(test_url)
        
        assert result is not None
        assert "Test Article Title" in result
        assert "AI and machine learning" in result
        assert len(result) > 100
    
    @responses.activate 
    def test_fetch_article_content_short_content(self):
        """Test article content fetching with short content"""
        test_url = "https://example.com/short"
        html_content = "<html><body><p>Short</p></body></html>"
        
        responses.add(
            responses.GET,
            test_url,
            body=html_content,
            status=200,
            content_type='text/html'
        )
        
        result = self.summarizer._fetch_article_content(test_url)
        
        assert result is None
    
    @responses.activate
    def test_fetch_article_content_failure(self):
        """Test article content fetching failure"""
        test_url = "https://example.com/notfound"
        
        responses.add(
            responses.GET,
            test_url,
            status=404
        )
        
        result = self.summarizer._fetch_article_content(test_url)
        
        assert result is None
    
    def test_create_summary_prompt(self):
        """Test summary prompt creation"""
        title = "AI Breakthrough in Machine Learning"
        content = "This article discusses the latest advances in artificial intelligence and machine learning technologies."
        
        prompt = self.summarizer._create_summary_prompt(title, content)
        
        assert title in prompt
        assert content in prompt
        assert "要約の要件" in prompt
        assert "日本語で出力" in prompt
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    @patch('os.unlink')
    def test_call_claude_cli_success(self, mock_unlink, mock_run, mock_tempfile):
        """Test successful Claude CLI call"""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test_prompt.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Mock subprocess success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="これはテスト要約です。AI技術について説明しています。"
        )
        
        prompt = "Test prompt for summarization"
        result = self.summarizer._call_claude_cli(prompt)
        
        assert result == "これはテスト要約です。AI技術について説明しています。"
        mock_run.assert_called_once_with(
            ["claude", "chat", "--file", "/tmp/test_prompt.txt"],
            capture_output=True,
            text=True,
            timeout=60
        )
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('subprocess.run')
    @patch('os.unlink')
    def test_call_claude_cli_failure(self, mock_unlink, mock_run, mock_tempfile):
        """Test Claude CLI call failure"""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test_prompt.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Mock subprocess failure
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Claude CLI error"
        )
        
        prompt = "Test prompt"
        result = self.summarizer._call_claude_cli(prompt)
        
        assert result is None
    
    @patch.object(ArticleSummarizer, '_check_claude_cli_availability')
    @patch.object(ArticleSummarizer, '_fetch_article_content')
    @patch.object(ArticleSummarizer, '_call_claude_cli')
    def test_summarize_article_success(self, mock_claude_cli, mock_fetch, mock_check):
        """Test successful article summarization"""
        # Mock dependencies
        mock_check.return_value = True
        mock_fetch.return_value = "Article content about AI technology"
        mock_claude_cli.return_value = "これはAI技術に関する記事の要約です。"
        
        title = "AI Breakthrough"
        url = "https://example.com/ai-news"
        
        result = self.summarizer.summarize_article(title, url)
        
        assert result['title'] == title
        assert result['url'] == url
        assert result['summary'] == "これはAI技術に関する記事の要約です。"
        assert result['summary_status'] == 'success'
        assert result['error'] is None
    
    @patch.object(ArticleSummarizer, '_check_claude_cli_availability')
    def test_summarize_article_claude_unavailable(self, mock_check):
        """Test article summarization when Claude CLI is unavailable"""
        mock_check.return_value = False
        
        result = self.summarizer.summarize_article("Test Title", "https://example.com")
        
        assert result['summary_status'] == 'failed'
        assert result['error'] == 'Claude CLI not available'
        assert result['summary'] == '要約機能は現在利用できません（Claude CLI未設定）'
    
    @patch.object(ArticleSummarizer, '_check_claude_cli_availability')
    @patch.object(ArticleSummarizer, '_fetch_article_content')
    def test_summarize_article_content_fetch_failure(self, mock_fetch, mock_check):
        """Test article summarization when content fetch fails"""
        mock_check.return_value = True
        mock_fetch.return_value = None
        
        result = self.summarizer.summarize_article("Test Title", "https://example.com")
        
        assert result['summary_status'] == 'failed'
        assert result['error'] == 'Failed to fetch article content'
        assert result['summary'] == '記事の内容を取得できませんでした'
    
    @patch.object(ArticleSummarizer, '_check_claude_cli_availability')
    def test_is_available(self, mock_check):
        """Test availability check"""
        mock_check.return_value = True
        assert self.summarizer.is_available() is True
        
        mock_check.return_value = False
        assert self.summarizer.is_available() is False
