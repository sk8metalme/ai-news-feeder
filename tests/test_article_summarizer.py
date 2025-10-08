"""
Tests for article summarizer module
"""
import pytest
import responses
from unittest.mock import Mock, patch, mock_open, ANY
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
        
        # Create a fresh instance after patching so __init__ picks up the mock
        summarizer = ArticleSummarizer()
        result = summarizer._check_claude_cli_availability()
        
        assert result is True
        # env は実装上 None を明示的に渡すため、ANY で許容
        mock_run.assert_called_once_with(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            env=ANY,
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
                    <p>This is a test article about AI and machine learning technology that is revolutionizing the world.</p>
                    <p>It contains multiple paragraphs with meaningful content that discusses various aspects of artificial intelligence.</p>
                    <p>The content should be long enough to pass the length check of 200 characters minimum requirement.</p>
                    <p>This additional paragraph ensures we have sufficient content for proper testing and validation.</p>
                    <p>Machine learning algorithms are becoming increasingly sophisticated and powerful in their applications.</p>
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
        assert len(result) > 200
    
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
        assert "この記事を日本語で3-4文に要約してください" in prompt
        assert "要約:" in prompt
    
    @patch('subprocess.run')
    def test_call_claude_cli_success(self, mock_run):
        """Test successful Claude CLI call"""
        # Mock subprocess success
        mock_run.return_value = Mock(
            returncode=0,
            stdout="これはテスト要約です。AI技術について説明しています。"
        )
        
        prompt = "Test prompt for summarization"
        result = self.summarizer._call_claude_cli(prompt)
        
        assert result == "これはテスト要約です。AI技術について説明しています。"
        # 最初の試行は 'args_print'（claude --print <prompt>）を想定
        called_args, called_kwargs = mock_run.call_args
        assert called_args[0][:2] == ["claude", "--print"]
        assert called_args[0][2] == "Test prompt for summarization"
        assert called_kwargs.get("capture_output") is True
        assert called_kwargs.get("text") is True
        assert called_kwargs.get("timeout") == 60
        # env は明示的に渡すため存在しているはず
        assert "env" in called_kwargs
    
    @patch('subprocess.run')
    def test_call_claude_cli_failure(self, mock_run):
        """Test Claude CLI call failure"""
        # Mock subprocess failure
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
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
