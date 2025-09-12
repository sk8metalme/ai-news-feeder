#!/usr/bin/env bash
# Install a user LaunchAgent that runs AI News Feeder under the logged-in session
# This allows Claude Code CLI to use interactive login credentials (no API key in .env).
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  $(basename "$0") --daily-at HH:MM    Install/replace a LaunchAgent that runs daily at HH:MM
  $(basename "$0") --interval SEC       Install/replace a LaunchAgent that runs every SEC seconds
  $(basename "$0") --remove             Unload and remove the LaunchAgent

Notes:
  - Installs to ~/Library/LaunchAgents/com.ai-news.feeder.plist
  - Runs in your logged-in user session (Keychain accessible) so Claude login works without ANTHROPIC_API_KEY
  - Uses your current repo path and system python3
USAGE
}

if [[ $# -lt 1 ]]; then usage; exit 1; fi

MODE=""
TIMEHH=""
TIMEMM=""
INTERVAL=""
RUN_AT_LOAD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --daily-at)
      shift
      [[ $# -gt 0 ]] || { echo "--daily-at requires HH:MM"; exit 1; }
      IFS=":" read -r TIMEHH TIMEMM <<<"$1" || true
      [[ "$TIMEHH" =~ ^[0-9]{1,2}$ && "$TIMEMM" =~ ^[0-9]{1,2}$ ]] || { echo "Invalid time format. Use HH:MM"; exit 1; }
      MODE="daily"; shift ;;
    --interval)
      shift
      [[ $# -gt 0 ]] || { echo "--interval requires seconds"; exit 1; }
      INTERVAL="$1"; [[ "$INTERVAL" =~ ^[0-9]+$ ]] || { echo "Invalid seconds"; exit 1; }
      MODE="interval"; shift ;;
    --no-run-at-load)
      RUN_AT_LOAD=0; shift ;;
    --remove)
      MODE="remove"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

LABEL="com.ai-news.feeder"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$LABEL.plist"

mkdir -p "$LAUNCH_AGENTS_DIR"

if [[ "$MODE" == "remove" ]]; then
  launchctl unload -w "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "Removed $PLIST_PATH"
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"

LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>cd "$REPO_ROOT" && export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH" LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8; "$PYTHON_BIN" main.py --run-once</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>CLAUDE_CLI_PATH</key>
    <string>${CLAUDE_CLI_PATH:-claude}</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/launchd.err.log</string>
PLIST

if [[ "$MODE" == "daily" ]]; then
  cat >> "$PLIST_PATH" <<PLIST
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>$TIMEHH</integer>
    <key>Minute</key>
    <integer>$TIMEMM</integer>
  </dict>
PLIST
elif [[ "$MODE" == "interval" ]]; then
  cat >> "$PLIST_PATH" <<PLIST
  <key>StartInterval</key>
  <integer>$INTERVAL</integer>
PLIST
fi

if [[ $RUN_AT_LOAD -eq 1 ]]; then
  cat >> "$PLIST_PATH" <<PLIST
  <key>RunAtLoad</key>
  <true/>
PLIST
fi

cat >> "$PLIST_PATH" <<PLIST
</dict>
</plist>
PLIST

launchctl unload -w "$PLIST_PATH" 2>/dev/null || true
launchctl load -w "$PLIST_PATH"
echo "LaunchAgent installed: $PLIST_PATH"
echo "To check status: launchctl list | grep $LABEL"
echo "Logs: $LOG_DIR/launchd.out.log, $LOG_DIR/launchd.err.log"
