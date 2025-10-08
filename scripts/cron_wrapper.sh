#!/bin/bash
# Cron wrapper script for AI News Feeder with environment variables

# Set working directory
cd /Users/arigatatsuya/Work/git/ai-news-feeder

# Load environment variables from .env file
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a  # stop automatically exporting
fi

# Set additional PATH for cron environment
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Set Python path
PYTHON_PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"

# Run the main script
$PYTHON_PATH main.py --run-once >> logs/cron.log 2>&1
