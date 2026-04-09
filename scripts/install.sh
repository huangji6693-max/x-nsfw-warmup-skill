#!/usr/bin/env bash
# X Warmup Skill · One-liner installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/huangji6693-max/x-nsfw-warmup-skill/main/scripts/install.sh | bash
#
# Or locally:
#   bash scripts/install.sh
#
# What it does:
#   1. Clone (or update) the skill into the right location for your AI client
#   2. Create a Python 3.10+ venv
#   3. Install requirements + Playwright Chromium
#   4. Run the prereq checker
#   5. Tell you exactly what command to run next

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

banner() {
  echo ""
  echo -e "${BOLD}🦞  X Warmup Skill · Installer${RESET}"
  echo    "================================="
  echo ""
}

# ============================================================================
# Prerequisites
# ============================================================================
check_prereq() {
  log "checking host prerequisites..."

  if ! command -v python3 &> /dev/null; then
    err "python3 not found. Install Python 3.10+ first:"
    echo "     macOS:  brew install python@3.11"
    echo "     Linux:  sudo apt install python3.11 python3.11-venv"
    exit 1
  fi

  local pyver
  pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  local major minor
  major=$(echo "$pyver" | cut -d. -f1)
  minor=$(echo "$pyver" | cut -d. -f2)
  if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 10 ]; }; then
    err "Python $pyver is too old. Need 3.10+."
    exit 1
  fi
  ok "python3 $pyver"

  if ! command -v git &> /dev/null; then
    err "git not found. Install git first."
    exit 1
  fi
  ok "git $(git --version | awk '{print $3}')"
}

# ============================================================================
# Pick install location based on detected AI client
# ============================================================================
pick_install_dir() {
  local custom_dir="${X_WARMUP_DIR:-}"

  if [ -n "$custom_dir" ]; then
    INSTALL_DIR="$custom_dir"
    log "using X_WARMUP_DIR=$INSTALL_DIR"
    return
  fi

  # Try OpenClaw first (workspace > global)
  if [ -d "$HOME/.openclaw/workspace/skills" ]; then
    INSTALL_DIR="$HOME/.openclaw/workspace/skills/x-nsfw-warmup"
    ok "OpenClaw workspace detected"
    return
  fi
  if [ -d "$HOME/.openclaw/skills" ]; then
    INSTALL_DIR="$HOME/.openclaw/skills/x-nsfw-warmup"
    ok "OpenClaw global detected"
    return
  fi

  # Then Claude Code
  if [ -d "$HOME/.claude/skills" ]; then
    INSTALL_DIR="$HOME/.claude/skills/x-nsfw-warmup"
    ok "Claude Code detected"
    return
  fi
  if [ -d "$HOME/.claude" ]; then
    INSTALL_DIR="$HOME/.claude/skills/x-nsfw-warmup"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    ok "Claude Code detected (skills dir created)"
    return
  fi

  # Fallback: standalone
  INSTALL_DIR="$HOME/x-warmup"
  warn "no AI client detected, falling back to $INSTALL_DIR"
}

# ============================================================================
# Clone or update
# ============================================================================
clone_repo() {
  local repo_url="https://github.com/huangji6693-max/x-nsfw-warmup-skill.git"

  if [ -d "$INSTALL_DIR/.git" ]; then
    log "updating existing install at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    git pull --ff-only || warn "git pull failed, continuing with current version"
  elif [ -d "$INSTALL_DIR" ] && [ -n "$(ls -A "$INSTALL_DIR" 2>/dev/null || true)" ]; then
    warn "$INSTALL_DIR already exists and is not a git repo"
    warn "skipping clone; assuming manual install"
    cd "$INSTALL_DIR"
  else
    log "cloning $repo_url → $INSTALL_DIR"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --depth=1 "$repo_url" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
  fi
  ok "repo ready at $INSTALL_DIR"
}

# ============================================================================
# venv + deps
# ============================================================================
setup_venv() {
  if [ ! -d .venv ]; then
    log "creating Python 3.11 venv..."
    python3 -m venv .venv
  else
    ok ".venv already exists"
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate

  log "upgrading pip..."
  pip install --quiet --upgrade pip

  log "installing requirements.txt (may take ~3 min)..."
  pip install --quiet -r requirements.txt
  ok "Python deps installed"

  log "installing Playwright Chromium (may take ~2 min)..."
  if ! playwright install chromium 2>&1 | tail -5; then
    warn "playwright install chromium failed; you can rerun later"
  else
    ok "Chromium installed"
  fi
}

# ============================================================================
# Run prereq checker
# ============================================================================
run_prereq_check() {
  if [ -f scripts/check_prereqs.py ]; then
    log "running prerequisite check..."
    echo ""
    python scripts/check_prereqs.py || true
  fi
}

# ============================================================================
# Next steps
# ============================================================================
print_next_steps() {
  echo ""
  echo "================================="
  echo -e "${GREEN}✅ Install complete.${RESET}"
  echo "================================="
  echo ""
  echo "Skill location:"
  echo "  $INSTALL_DIR"
  echo ""
  echo "Next step — onboard your existing accounts:"
  echo ""
  echo -e "  ${BOLD}cd $INSTALL_DIR${RESET}"
  echo -e "  ${BOLD}source .venv/bin/activate${RESET}"
  echo -e "  ${BOLD}python scripts/onboard.py${RESET}"
  echo ""
  echo "The onboarding wizard will:"
  echo "  - connect to your AdsPower (or other fingerprint browser)"
  echo "  - import your existing profiles"
  echo "  - ask you to enter the X handle for each"
  echo "  - populate warmup.db"
  echo "  - then tell you how to go live"
  echo ""
  echo "If you don't use AdsPower, read deploy/README.md instead."
  echo ""
}

# ============================================================================
# main
# ============================================================================
main() {
  banner
  check_prereq
  pick_install_dir
  clone_repo
  setup_venv
  run_prereq_check
  print_next_steps
}

main "$@"
