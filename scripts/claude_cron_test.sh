#!/usr/bin/env bash
# Minimal cron-safe tester for Claude Code CLI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

mkdir -p logs
DT="$(date +%Y%m%d_%H%M%S)"
OUT="logs/claude_cron_test_${DT}.out"
ERR="logs/claude_cron_test_${DT}.err"
META="logs/claude_cron_test_${DT}.meta"

# Ensure cron-safe PATH and locale
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

# Load .env if present so ANTHROPIC_API_KEY is available
set +u
if [[ -f ./.env ]]; then
  set -a; . ./.env; set +a
fi
set -u

BIN="${CLAUDE_CLI_PATH:-claude}"
PROMPT="こんにちは。これはcron経由のClaude動作確認です。3文以内で応答してください。"

{
  echo "[meta] started_at=$(date -Iseconds)"
  echo "[meta] pwd=$PWD"
  echo "[meta] whoami=$(whoami 2>/dev/null || true)"
  echo "[meta] shell=$SHELL"
  echo "[meta] PATH=$PATH"
  echo "[meta] LANG=$LANG LC_ALL=$LC_ALL"
  echo "[meta] BIN=$BIN"
  echo "[meta] which=$(command -v "$BIN" || true)"
  echo "[meta] version=$($BIN --version 2>&1 || echo 'N/A')"
  if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "[meta] ANTHROPIC_API_KEY=present(len=${#ANTHROPIC_API_KEY})"
  else
    echo "[meta] ANTHROPIC_API_KEY=missing"
  fi
} >"$META" 2>/dev/null

set +e
$BIN -p "$PROMPT" --output-format text >"$OUT" 2>"$ERR"
RC=$?
set -e

{
  echo "[meta] rc=$RC"
  echo "[meta] out_size=$(wc -c < "$OUT" 2>/dev/null || echo 0)"
  echo "[meta] err_size=$(wc -c < "$ERR" 2>/dev/null || echo 0)"
  echo "[meta] finished_at=$(date -Iseconds)"
} >>"$META" 2>/dev/null

echo "Claude cron test complete. rc=$RC"
echo "- OUT:  $OUT"
echo "- ERR:  $ERR"
echo "- META: $META"

