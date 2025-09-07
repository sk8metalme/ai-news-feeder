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
from src.utils.health_checker import HealthChecker
from src.notification.slack_notifier import SlackNotifier
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='AI News Feeder Bot')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run verification once and exit')
    parser.add_argument('--schedule', action='store_true', default=True,
                       help='Run with scheduler (default)')
    parser.add_argument('--health-check', action='store_true',
                       help='Run system health check and exit')
    
    args = parser.parse_args()
    
    try:
        if args.health_check:
            logger.info("Running system health check...")
            health_checker = HealthChecker()
            health_data = health_checker.run_full_health_check()
            
            # Print health report to console
            report = health_checker.format_health_report(health_data)
            print(report)
            
            # Send health report to Slack if configured
            try:
                notifier = SlackNotifier()
                if notifier.webhook_url:
                    notifier.send_notification(report)
                    logger.info("Health report sent to Slack")
                else:
                    logger.info("Slack not configured, health report displayed only")
            except Exception as e:
                logger.warning(f"Failed to send health report to Slack: {e}")
            
            # Exit with appropriate code based on health status
            if health_data['overall_status'] == 'healthy':
                sys.exit(0)
            elif health_data['overall_status'] == 'degraded':
                sys.exit(1)
            else:  # unhealthy
                sys.exit(2)
        
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
