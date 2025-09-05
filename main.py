#!/usr/bin/env python3
"""
AI News Feeder - Main entry point
"""
import sys
import os
import argparse

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scheduler import AINewsScheduler
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='AI News Feeder Bot')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run verification once and exit')
    parser.add_argument('--schedule', action='store_true', default=True,
                       help='Run with scheduler (default)')
    
    args = parser.parse_args()
    
    try:
        scheduler = AINewsScheduler()
        
        if args.run_once:
            logger.info("Running single verification job")
            scheduler.run_verification_job()
        else:
            logger.info("Starting scheduled mode")
            scheduler.start_scheduler()
            
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
