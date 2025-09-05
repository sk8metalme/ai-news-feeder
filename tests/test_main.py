"""
Tests for main application entry point
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import main


class TestMain:
    """Test cases for main application"""
    
    @patch('main.AINewsScheduler')
    @patch('sys.argv', ['main.py', '--run-once'])
    def test_main_run_once(self, mock_scheduler_class):
        """Test main function with --run-once flag"""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        main.main()
        
        # Verify scheduler was created and run_once was called
        mock_scheduler_class.assert_called_once()
        mock_scheduler.run_verification_job.assert_called_once()
        mock_scheduler.start_scheduler.assert_not_called()
    
    @patch('main.AINewsScheduler')
    @patch('sys.argv', ['main.py', '--schedule'])
    def test_main_schedule(self, mock_scheduler_class):
        """Test main function with --schedule flag"""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        main.main()
        
        # Verify scheduler was created and start_scheduler was called
        mock_scheduler_class.assert_called_once()
        mock_scheduler.start_scheduler.assert_called_once()
        mock_scheduler.run_verification_job.assert_not_called()
    
    @patch('main.AINewsScheduler')
    @patch('sys.argv', ['main.py'])  # Default behavior
    def test_main_default(self, mock_scheduler_class):
        """Test main function with default behavior"""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        main.main()
        
        # Default should be schedule mode
        mock_scheduler_class.assert_called_once()
        mock_scheduler.start_scheduler.assert_called_once()
    
    @patch('main.AINewsScheduler')
    @patch('sys.argv', ['main.py', '--run-once'])
    def test_main_keyboard_interrupt(self, mock_scheduler_class):
        """Test main function handling KeyboardInterrupt"""
        mock_scheduler = Mock()
        mock_scheduler.run_verification_job.side_effect = KeyboardInterrupt()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Should not raise exception
        main.main()
        
        mock_scheduler.run_verification_job.assert_called_once()
    
    @patch('main.AINewsScheduler')
    @patch('sys.argv', ['main.py', '--run-once'])
    @patch('sys.exit')
    def test_main_exception_handling(self, mock_exit, mock_scheduler_class):
        """Test main function handling general exceptions"""
        mock_scheduler = Mock()
        mock_scheduler.run_verification_job.side_effect = Exception("Test error")
        mock_scheduler_class.return_value = mock_scheduler
        
        main.main()
        
        # Should call sys.exit(1) on exception
        mock_exit.assert_called_once_with(1)
