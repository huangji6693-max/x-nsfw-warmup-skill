#!/usr/bin/env bash
# X Warmup Skill · GUI launcher
#
# Handles venv activation, dependency check, and starts the NiceGUI panel.
#
# Usage:
#   bash scripts/launch_gui.sh

set -euo pipefail

# ============================================================================
# Colors
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

log()  { echo -e "${BLUE}[*]${RESET} $1"; }
ok()   { echo -e "${GREEN}[+]${RESET} $1"; }
warn() { echo -e "${YELLOW}[!]${RESET} $1"; }
err()  { echo -e "${RED}[x]${RESET} $1"; }

# ============================================================================
# Find repo root (2 levels up from this script)
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo -e "${BOLD}🦞  X Warmup Skill · GUI Launcher${RESET}"
echo    "=================================="
echo ""

# ============================================================================
# Activate venv
# ============================================================================
if [ ! -d .venv ]; then
  err ".venv not found. Run scripts/install.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
ok "activated venv at $(pwd)/.venv"

# ============================================================================
# Check GUI deps
# ============================================================================
if ! python -c "import nicegui" 2>/dev/null; then
  log "nicegui not installed, installing gui/requirements.txt..."
  pip install --quiet -r gui/requirements.txt
  ok "nicegui installed"
else
  ok "nicegui already installed"
fi

if ! python -c "import requests" 2>/dev/null; then
  log "requests not installed, installing..."
  pip install --quiet requests
fi

# ============================================================================
# Launch
# ============================================================================
echo ""
log "launching control panel..."
log "will open at http://localhost:8080"
log "press Ctrl+C to stop"
echo ""

python gui/app.py
