#!/bin/bash
# Cron setup script for AI News Feeder

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

# Create cron job entry
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH main.py --run-once >> logs/cron.log 2>&1"

# Add to crontab
echo "Setting up cron job for AI News Feeder..."
echo "Job will run daily at 9:00 AM"
echo "Cron entry: $CRON_JOB"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "ai-news-feeder"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "ai-news-feeder" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "# AI News Feeder - Daily verification at 9:00 AM"; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully!"
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the AI News Feeder lines)"
