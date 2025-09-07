"""
Logging utility for AI News Feeder
"""
import logging
import os
from datetime import datetime
from config.settings import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    """Create and configure a logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Set log level
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = os.path.join(LOG_DIR, f"ai_news_feeder_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger


def setup_logger(name: str) -> logging.Logger:
    """ロガーをセットアップして返す（get_loggerのエイリアス）"""
    return get_logger(name)
