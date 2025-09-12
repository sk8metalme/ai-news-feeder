#!/usr/bin/env bash
# Quick doctor script to verify the official Anthropic Claude CLI is installed and usable
set -euo pipefail

BIN=${CLAUDE_CLI_PATH:-claude}

color() { printf "\033[%sm%s\033[0m\n" "$1" "$2"; }
ok() { color 32 "✔ $1"; }
warn() { color 33 "⚠ $1"; }
err() { color 31 "✖ $1"; }

echo "[1/6] Resolving CLI path..."
CLAUDE_PATH="$(command -v "$BIN" || true)"
if [[ -z "$CLAUDE_PATH" ]]; then
  err "Could not find '$BIN' on PATH. Set CLAUDE_CLI_PATH or install official CLI."
  exit 2
fi
ok "Using: $CLAUDE_PATH"

echo "[2/6] Checking version..."
set +e
VERSION_OUT="$($CLAUDE_PATH --version 2>&1)"; RC=$?
set -e
if [[ $RC -ne 0 ]]; then
  err "'claude --version' failed (rc=$RC): $VERSION_OUT"
  exit 2
fi
echo "  -> $VERSION_OUT"
if echo "$VERSION_OUT" | grep -qi "Claude Code"; then
  warn "Detected 'Claude Code' variant. This IDE helper is not supported for headless summarization."
  echo "    - Install the official Anthropic Claude CLI (see README)"
  echo "    - Or set CLAUDE_CLI_PATH to point to the official binary"
  exit 3
fi
ok "Looks like the official CLI variant"

echo "[3/6] Checking available subcommands..."
HELP_OUT="$($CLAUDE_PATH --help 2>&1 || true)"
if ! echo "$HELP_OUT" | grep -q "chat"; then
  warn "'chat' subcommand not visible in --help. CLI may be outdated."
else
  ok "'chat' subcommand available"
fi

echo "[4/6] Probing non-interactive '-p' support..."
set +e
$CLAUDE_PATH -p "ping" --output-format text >/dev/null 2>&1
RC=$?
set -e
if [[ $RC -ne 0 ]]; then
  warn "'claude -p' returned rc=$RC. If this persists, re-install CLI and run 'claude configure'."
else
  ok "'claude -p' accepted"
fi

echo "[5/6] Environment check..."
if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  ok "ANTHROPIC_API_KEY is set in environment"
else
  warn "ANTHROPIC_API_KEY not set in environment. 'claude configure' usually stores credentials; that's OK."
fi

echo "[6/6] PATH preview (cron-safe)..."
echo "  PATH=$PATH"
ok "Doctor completed. If warnings remain, follow README steps to reinstall and configure the official CLI."
