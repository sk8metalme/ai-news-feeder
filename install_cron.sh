#!/bin/bash
# Cron setup script for AI News Feeder

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)

usage() {
  cat <<USAGE
Usage:
  $(basename "$0")                       # install daily job at 09:00
  $(basename "$0") --run-in-minutes N    # install one-off job to run in N minutes
  $(basename "$0") --claude-test-in-minutes N  # schedule claude_cron_test.sh in N minutes

Notes:
  - Injects PATH with common Homebrew locations so 'claude' is discoverable.
  - One-off job self-removes from crontab after it runs.
USAGE
}

ONE_OFF_MINUTES=""
CLAUDE_TEST_MINUTES=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-in-minutes)
      ONE_OFF_MINUTES="$2"; shift 2 ;;
    --claude-test-in-minutes)
      CLAUDE_TEST_MINUTES="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

DEFAULT_PATHS="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# Ensure UTF-8 locale for proper Japanese I/O in non-interactive cron
CRON_ENV="PATH=$DEFAULT_PATHS LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8"
# Load .env at runtime so secrets like ANTHROPIC_API_KEY are available to Python and subprocesses
ENV_LOAD='set -a; [ -f ./.env ] && . ./.env; set +a'

if [[ -n "$ONE_OFF_MINUTES" ]]; then
  if ! [[ "$ONE_OFF_MINUTES" =~ ^[0-9]+$ ]]; then
    echo "ERROR: --run-in-minutes expects a positive integer" >&2
    exit 1
  fi
  # Compute run time for both macOS (BSD date) and Linux (GNU date)
  if date -v +1M +%s >/dev/null 2>&1; then
    # macOS / BSD date
    RUN_AT=$(date -v+"${ONE_OFF_MINUTES}"M +"%M %H %d %m %Y%m%d%H%M")
  else
    # GNU date (Linux)
    RUN_AT=$(date -d "+${ONE_OFF_MINUTES} minutes" +"%M %H %d %m %Y%m%d%H%M")
  fi
  CRON_MIN=$(echo "$RUN_AT" | awk '{print $1}')
  CRON_HOUR=$(echo "$RUN_AT" | awk '{print $2}')
  CRON_DOM=$(echo "$RUN_AT" | awk '{print $3}')
  CRON_MON=$(echo "$RUN_AT" | awk '{print $4}')
  ONE_OFF_ID=$(echo "$RUN_AT" | awk '{print $5}')

  echo "Installing one-off cron job to run in $ONE_OFF_MINUTES minute(s)..."
  echo "Run at: $(printf '%s:%s on %s/%s' "$CRON_HOUR" "$CRON_MIN" "$CRON_MON" "$CRON_DOM")"

  ONE_OFF_LINE="$CRON_MIN $CRON_HOUR $CRON_DOM $CRON_MON * cd $SCRIPT_DIR && $CRON_ENV bash -lc '$ENV_LOAD; $PYTHON_PATH main.py --run-once' >> logs/cron.log 2>&1; /usr/bin/crontab -l 2>/dev/null | /usr/bin/grep -v AI_NEWS_FEEDER_ONE_OFF_$ONE_OFF_ID | /usr/bin/crontab - # AI_NEWS_FEEDER_ONE_OFF_$ONE_OFF_ID"

  # Append one-off job
  (crontab -l 2>/dev/null; echo "$ONE_OFF_LINE") | crontab -
  echo "One-off cron job installed (ID: AI_NEWS_FEEDER_ONE_OFF_$ONE_OFF_ID)"
  exit 0
fi

# Otherwise, install or replace the daily job at 09:00
CRON_JOB="0 9 * * * cd $SCRIPT_DIR && $CRON_ENV bash -lc '$ENV_LOAD; $PYTHON_PATH main.py --run-once' >> logs/cron.log 2>&1"

# Add to crontab
echo "Setting up cron job for AI News Feeder..."
echo "Job will run daily at 9:00 AM"
echo "Cron entry: $CRON_JOB"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -qi "AI News Feeder - Daily"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -vi "AI News Feeder - Daily" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "# AI News Feeder - Daily verification at 9:00 AM"; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully!"
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the AI News Feeder lines)"
if [[ -n "$CLAUDE_TEST_MINUTES" ]]; then
  if ! [[ "$CLAUDE_TEST_MINUTES" =~ ^[0-9]+$ ]]; then
    echo "ERROR: --claude-test-in-minutes expects a positive integer" >&2
    exit 1
  fi
  if date -v +1M +%s >/dev/null 2>&1; then
    RUN_AT=$(date -v+"${CLAUDE_TEST_MINUTES}"M +"%M %H %d %m %Y%m%d%H%M")
  else
    RUN_AT=$(date -d "+${CLAUDE_TEST_MINUTES} minutes" +"%M %H %d %m %Y%m%d%H%M")
  fi
  CRON_MIN=$(echo "$RUN_AT" | awk '{print $1}')
  CRON_HOUR=$(echo "$RUN_AT" | awk '{print $2}')
  CRON_DOM=$(echo "$RUN_AT" | awk '{print $3}')
  CRON_MON=$(echo "$RUN_AT" | awk '{print $4}')
  ONE_OFF_ID=$(echo "$RUN_AT" | awk '{print $5}')

  echo "Installing CLAUDE cron test to run in $CLAUDE_TEST_MINUTES minute(s)..."
  echo "Run at: $(printf '%s:%s on %s/%s' "$CRON_HOUR" "$CRON_MIN" "$CRON_MON" "$CRON_DOM")"

  TEST_LINE="$CRON_MIN $CRON_HOUR $CRON_DOM $CRON_MON * cd $SCRIPT_DIR && $CRON_ENV bash -lc '$ENV_LOAD; ./scripts/claude_cron_test.sh' >> logs/cron_test.log 2>&1; /usr/bin/crontab -l 2>/dev/null | /usr/bin/grep -v AI_NEWS_FEEDER_CLAUDE_TEST_$ONE_OFF_ID | /usr/bin/crontab - # AI_NEWS_FEEDER_CLAUDE_TEST_$ONE_OFF_ID"

  (crontab -l 2>/dev/null; echo "$TEST_LINE") | crontab -
  echo "Claude cron test job installed (ID: AI_NEWS_FEEDER_CLAUDE_TEST_$ONE_OFF_ID)"
  exit 0
fi
