#!/usr/bin/env python3
"""
X Warmup Skill · Interactive Onboarding Wizard

For users who already have:
  - A fingerprint browser (AdsPower recommended, BitBrowser supported)
  - Existing X accounts already logged into those profiles
  - (Optional) Cookies / proxies already configured in the fingerprint browser

This wizard will:
  1. Detect and connect to your fingerprint browser's Local API
  2. List your existing profiles
  3. Ask you to confirm which profiles to import + their X handles
  4. Write everything into warmup.db
  5. Tell you the exact commands to run next

Usage:
    python scripts/onboard.py
    python scripts/onboard.py --db /path/to/warmup.db
    python scripts/onboard.py --adspower http://localhost:50325
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


# ============================================================================
# Colors
# ============================================================================
IS_TTY = sys.stdout.isatty()
GREEN = "\033[92m" if IS_TTY else ""
RED = "\033[91m" if IS_TTY else ""
YELLOW = "\033[93m" if IS_TTY else ""
BLUE = "\033[94m" if IS_TTY else ""
BOLD = "\033[1m" if IS_TTY else ""
DIM = "\033[2m" if IS_TTY else ""
RESET = "\033[0m" if IS_TTY else ""


def banner():
    print()
    print(f"{BOLD}🦞  X Warmup Skill · Onboarding Wizard{RESET}")
    print(f"{BOLD}{'=' * 42}{RESET}")
    print("For users who already have accounts + a fingerprint browser.")
    print()


def step(n: int, total: int, title: str):
    print()
    print(f"{BOLD}{BLUE}[{n}/{total}] {title}{RESET}")
    print(f"{DIM}{'─' * 42}{RESET}")


def prompt(text: str, default: str | None = None) -> str:
    hint = f" {DIM}[{default}]{RESET}" if default else ""
    answer = input(f"  {text}{hint}\n  > ").strip()
    return answer or (default or "")


def prompt_yn(text: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    answer = input(f"  {text} [{d}] > ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def info(msg: str):
    print(f"  {BLUE}[*]{RESET} {msg}")


def ok(msg: str):
    print(f"  {GREEN}[+]{RESET} {msg}")


def err(msg: str):
    print(f"  {RED}[x]{RESET} {msg}")


# ============================================================================
# Data classes
# ============================================================================
@dataclass
class FingerprintProfile:
    browser: str            # "adspower" | "bitbrowser" | "manual"
    profile_id: str         # browser-native profile ID
    name: str               # friendly name in browser
    x_handle: str = ""      # filled by user
    proxy_url: str = ""     # optional override
    notes: str = ""


# ============================================================================
# AdsPower
# ============================================================================
def adspower_list(url: str) -> list[dict[str, Any]]:
    import requests
    r = requests.get(
        f"{url}/api/v1/user/list",
        params={"page": 1, "page_size": 200},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"AdsPower API error: {data}")
    return data.get("data", {}).get("list", [])


# ============================================================================
# BitBrowser
# ============================================================================
def bitbrowser_list(url: str) -> list[dict[str, Any]]:
    import requests
    r = requests.post(
        f"{url}/browser/list",
        json={"page": 0, "pageSize": 200},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise RuntimeError(f"BitBrowser API error: {data}")
    return data.get("data", {}).get("list", [])


# ============================================================================
# Steps
# ============================================================================
def step_pick_browser() -> tuple[str, str]:
    """Returns (browser_kind, api_url)"""
    step(1, 5, "Which fingerprint browser do you use?")
    print("  [1] AdsPower  (Local API at http://local.adspower.net:50325)")
    print("  [2] BitBrowser (Local API at http://127.0.0.1:54345)")
    print("  [3] Other / manual (patchright, Multilogin, Dolphin Anty, etc.)")
    print()

    choice = prompt("Enter 1, 2, or 3")
    if choice == "1":
        default_url = "http://local.adspower.net:50325"
        url = prompt("AdsPower Local API URL", default=default_url)
        return "adspower", url
    if choice == "2":
        default_url = "http://127.0.0.1:54345"
        url = prompt("BitBrowser Local API URL", default=default_url)
        return "bitbrowser", url
    return "manual", ""


def step_connect_and_list(browser: str, api_url: str) -> list[FingerprintProfile]:
    step(2, 5, f"Connect to {browser} + list profiles")
    profiles: list[FingerprintProfile] = []

    if browser == "adspower":
        try:
            info(f"calling {api_url}/api/v1/user/list ...")
            raw = adspower_list(api_url)
            ok(f"connected · found {len(raw)} profile(s)")
            for p in raw:
                profiles.append(FingerprintProfile(
                    browser="adspower",
                    profile_id=p.get("user_id", ""),
                    name=p.get("name") or p.get("user_id", "unnamed"),
                ))
        except Exception as e:
            err(f"can't connect: {e}")
            err("troubleshooting:")
            print("    1. Is AdsPower desktop running?")
            print("    2. Settings → API → Local API is enabled?")
            print("    3. Is the URL correct?")
            sys.exit(1)

    elif browser == "bitbrowser":
        try:
            info(f"calling {api_url}/browser/list ...")
            raw = bitbrowser_list(api_url)
            ok(f"connected · found {len(raw)} profile(s)")
            for p in raw:
                profiles.append(FingerprintProfile(
                    browser="bitbrowser",
                    profile_id=str(p.get("id", "")),
                    name=p.get("name") or str(p.get("id", "unnamed")),
                ))
        except Exception as e:
            err(f"can't connect: {e}")
            sys.exit(1)

    else:
        info("manual mode — you'll type in profile details yourself")
        while True:
            name = prompt("profile name (blank to finish)")
            if not name:
                break
            pid = prompt(f"profile ID for {name}")
            profiles.append(FingerprintProfile(
                browser="manual",
                profile_id=pid,
                name=name,
            ))

    return profiles


def step_pick_profiles(profiles: list[FingerprintProfile]) -> list[FingerprintProfile]:
    step(3, 5, "Pick which profiles to import")
    if not profiles:
        err("no profiles to pick from")
        sys.exit(1)

    for i, p in enumerate(profiles, 1):
        print(f"  [{i:>2}] {p.name:<30} {DIM}id={p.profile_id}{RESET}")
    print()
    print(f"  [{BOLD}a{RESET}] all ({len(profiles)})")
    print(f"  [{BOLD}m{RESET}] manual pick (comma-separated numbers, e.g. 1,3,5)")
    print()

    choice = prompt("your pick").lower()
    if choice == "a":
        return profiles
    if choice == "m":
        raw = prompt("numbers")
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
        except ValueError:
            err("invalid numbers, exiting")
            sys.exit(1)
        return [profiles[i] for i in indices if 0 <= i < len(profiles)]
    # single number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(profiles):
            return [profiles[idx]]
    except ValueError:
        pass
    err("invalid choice, exiting")
    sys.exit(1)


def step_fill_handles(picked: list[FingerprintProfile]) -> list[FingerprintProfile]:
    step(4, 5, "Enter X handle for each profile")
    print("  (leave blank to skip a profile)")
    print("  (@ symbol is optional, will be stripped)")
    print()

    filled: list[FingerprintProfile] = []
    for p in picked:
        handle = prompt(f"  {p.name} → @").lstrip("@")
        if not handle:
            info(f"  skipped {p.name}")
            continue
        p.x_handle = handle
        filled.append(p)
        ok(f"  → @{handle}")

    return filled


def step_write_db(db_path: Path, accounts: list[FingerprintProfile]) -> int:
    step(5, 5, "Write to warmup.db")
    info(f"database: {db_path.resolve()}")

    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            handle TEXT PRIMARY KEY,
            email TEXT,
            password TEXT,
            cookies_path TEXT,
            proxy_url TEXT,
            fingerprint_profile_id TEXT NOT NULL,
            fingerprint_browser TEXT DEFAULT 'adspower',
            status TEXT DEFAULT 'active',
            cooldown_until TIMESTAMP,
            last_warmup_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS creators (
            handle TEXT PRIMARY KEY,
            followers INTEGER,
            bio TEXT,
            nsfw_score REAL,
            follow_priority INTEGER DEFAULT 5,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_path TEXT UNIQUE,
            content_level INTEGER,
            nsfw_labels TEXT,
            posted_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS follow_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            target_handle TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    inserted = 0
    updated = 0
    for a in accounts:
        existing = conn.execute(
            "SELECT handle FROM accounts WHERE handle = ?", (a.x_handle,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE accounts
                   SET fingerprint_profile_id = ?,
                       fingerprint_browser = ?,
                       proxy_url = ?,
                       notes = ?,
                       status = 'active'
                   WHERE handle = ?""",
                (a.profile_id, a.browser, a.proxy_url, a.notes, a.x_handle),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO accounts
                   (handle, fingerprint_profile_id, fingerprint_browser, proxy_url, notes, status)
                   VALUES (?, ?, ?, ?, ?, 'active')""",
                (a.x_handle, a.profile_id, a.browser, a.proxy_url, a.notes),
            )
            inserted += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'").fetchone()[0]
    conn.close()

    ok(f"inserted {inserted} new, updated {updated} existing")
    ok(f"total active accounts in DB: {total}")
    return total


def print_next_steps(repo_root: Path, total_accounts: int):
    print()
    print(f"{BOLD}{'=' * 42}{RESET}")
    print(f"{GREEN}{BOLD}✅ Onboarding complete{RESET}")
    print(f"{BOLD}{'=' * 42}{RESET}")
    print()
    print(f"  {BOLD}{total_accounts}{RESET} account(s) ready in warmup.db")
    print()
    print(f"{BOLD}Next steps:{RESET}")
    print()
    print(f"  {BLUE}1.{RESET} Verify everything dry-run:")
    print(f"     python scripts/check_prereqs.py")
    print()
    print(f"  {BLUE}2.{RESET} Walk through the loop (safe, no real actions):")
    print(f"     python examples/05-full-warmup-loop.py --dry-run")
    print()
    print(f"  {BLUE}3.{RESET} Add creators (optional, improves warmup quality):")
    print(f"     python scripts/seed_creators.py --from-file handles.txt")
    print()
    print(f"  {BLUE}4.{RESET} Add media items (optional; needed for post_tweet action):")
    print(f"     python examples/02-nudenet-classify.py path/to/media/dir")
    print()
    print(f"  {BLUE}5.{RESET} When you're READY to go live:")
    print(f"     {YELLOW}cp deploy/.env.example .env{RESET}")
    print(f"     {YELLOW}# edit .env: WARMUP_MODE=live I_UNDERSTAND_THE_RISKS=yes{RESET}")
    print(f"     {YELLOW}python deploy/scripts/run_live.py{RESET}")
    print()
    print(f"  {BLUE}6.{RESET} Or for 24/7 systemd/docker deployment:")
    print(f"     see deploy/README.md")
    print()
    print(f"{BOLD}{'=' * 42}{RESET}")
    print()
    print(f"{DIM}Pro tip: tell your AI assistant (OpenClaw / Claude Code):{RESET}")
    print(f"{DIM}  \"read AI-AGENT-PLAYBOOK.md, then explain what's still missing\"{RESET}")
    print()


# ============================================================================
# Main
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="X Warmup Skill onboarding wizard")
    parser.add_argument("--db", default="warmup.db", help="path to warmup.db (default: warmup.db)")
    parser.add_argument("--adspower", help="AdsPower Local API URL (skip interactive picker)")
    parser.add_argument("--all", action="store_true", help="import all profiles (skip pick step)")
    args = parser.parse_args()

    banner()

    # Step 1 — pick browser
    if args.adspower:
        browser, api_url = "adspower", args.adspower
        info(f"non-interactive: using AdsPower at {api_url}")
    else:
        browser, api_url = step_pick_browser()

    # Step 2 — connect + list
    profiles = step_connect_and_list(browser, api_url)
    if not profiles:
        err("no profiles found, exiting")
        sys.exit(1)

    # Step 3 — pick profiles to import
    if args.all:
        picked = profiles
        info(f"non-interactive --all: importing all {len(profiles)} profiles")
    else:
        picked = step_pick_profiles(profiles)

    if not picked:
        err("no profiles selected, exiting")
        sys.exit(1)

    # Step 4 — fill X handles
    filled = step_fill_handles(picked)
    if not filled:
        err("no handles entered, exiting")
        sys.exit(1)

    # Step 5 — write DB
    total = step_write_db(Path(args.db), filled)

    # Final
    print_next_steps(Path(__file__).resolve().parents[1], total)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted.")
        sys.exit(130)
