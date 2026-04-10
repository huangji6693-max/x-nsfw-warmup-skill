#!/usr/bin/env bash
# X Warmup Skill · GUI launcher with caffeinate (keep Mac awake)
#
# This is the same as launch_gui.sh but wraps the panel in `caffeinate`
# so your Mac won't sleep while the loop is running.
#
# WARNING:
#   - Only use this when your Mac is plugged in (sleep on battery is fine)
#   - Don't use this on a MacBook 24/7 — it will damage battery health
#   - Stop the panel = caffeinate exits = Mac resumes normal sleep behavior
#
# Usage:
#   bash scripts/launch_gui_keepawake.sh

set -euo pipefail

if ! command -v caffeinate &> /dev/null; then
  echo "[!] caffeinate not found. This script only works on macOS."
  echo "[!] Falling back to launch_gui.sh without keep-awake..."
  exec "$(dirname "$0")/launch_gui.sh"
fi

echo ""
echo "🦞  X Warmup Skill · GUI Launcher (keep-awake mode)"
echo "===================================================="
echo ""
echo "⚠️  This will prevent your Mac from sleeping while running."
echo "⚠️  Recommended only when plugged into power."
echo "⚠️  Press Ctrl+C to stop and let Mac sleep normally."
echo ""

# -i prevent idle sleep, -s prevent sleep when on AC power
exec caffeinate -i -s bash "$(dirname "$0")/launch_gui.sh"
