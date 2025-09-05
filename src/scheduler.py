"""
Scheduler module for running AI news verification tasks
"""
import schedule
import time
import os
from datetime import datetime
from .api.hacker_news import HackerNewsAPI
from .verification.fact_checker import FactChecker
from .notification.slack_notifier import SlackNotifier
from .utils.report_generator import ReportGenerator
from .utils.logger import get_logger
from config.settings import CHECK_INTERVAL_HOURS, MAX_ARTICLES_PER_DAY

logger = get_logger(__name__)


class AINewsScheduler:
    """Main scheduler class for AI news verification"""
    
    def __init__(self):
        self.hn_api = HackerNewsAPI()
        self.fact_checker = FactChecker()
        self.slack_notifier = SlackNotifier()
        self.report_generator = ReportGenerator()
        
    def run_verification_job(self):
        """Run the main verification job"""
        logger.info("Starting AI news verification job")
        start_time = datetime.now()
        
        try:
            # Fetch AI-related stories from Hacker News
            ai_stories = self.hn_api.get_ai_stories(
                max_stories=200, 
                hours=CHECK_INTERVAL_HOURS
            )
            
            if not ai_stories:
                logger.info("No AI stories found")
                return
            
            # Limit to MAX_ARTICLES_PER_DAY
            stories_to_verify = ai_stories[:MAX_ARTICLES_PER_DAY]
            verification_results = []
            
            for story in stories_to_verify:
                title = story.get('title', 'No title')
                url = story.get('url', f"https://news.ycombinator.com/item?id={story.get('id')}")
                
                # Verify the article
                result = self.fact_checker.verify_article(title, url)
                result['hacker_news_score'] = story.get('score', 0)
                verification_results.append(result)
                
                # Send individual notification for verified articles
                if result.get('verification_status') == 'verified':
                    self.slack_notifier.send_verification_report(result)
                
                # Add delay between verifications
                time.sleep(2)
            
            # Save daily report
            self.report_generator.save_daily_report(verification_results)
            
            # Send daily summary
            self.slack_notifier.send_daily_summary(verification_results)
            
            # Log completion
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            stats = self.report_generator.generate_summary_stats(verification_results)
            
            logger.info(f"Verification job completed in {duration:.2f} seconds")
            logger.info(f"Processed {stats['total_articles']} articles, "
                       f"verified {stats['verified_articles']} "
                       f"({stats['verification_rate']}%)")
            
        except Exception as e:
            logger.error(f"Error in verification job: {e}")
            # Send error notification to Slack
            error_message = f"🚨 AI News Bot Error\n\nError occurred during verification job:\n{str(e)}"
            self.slack_notifier.send_notification(error_message)
    
    def start_scheduler(self):
        """Start the scheduled job"""
        logger.info("Starting AI News Scheduler")
        
        # Schedule daily job at 9:00 AM
        schedule.every().day.at("09:00").do(self.run_verification_job)
        
        # Also allow manual triggering for testing
        logger.info("Job scheduled for daily execution at 09:00")
        logger.info("Running initial verification job...")
        
        # Run once immediately for testing
        self.run_verification_job()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    try:
        scheduler = AINewsScheduler()
        scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")


if __name__ == "__main__":
    main()
