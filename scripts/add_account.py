#!/usr/bin/env python3
"""
X Warmup Skill · Add Single Account

CLI to add one account to warmup.db. Useful for scripting / CI / adding
one-off accounts without running the full onboard wizard.

Usage:
    python scripts/add_account.py \
        --handle alice_cute \
        --profile-id ads_profile_abc123 \
        --browser adspower

    python scripts/add_account.py \
        --handle bob_xx \
        --profile-id bb_456 \
        --browser bitbrowser \
        --proxy http://user:pass@host:port \
        --cookies cookies/bob.json \
        --notes "bought 2025-12, VN number"
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


SCHEMA_SQL = """
-- 不存密码：仅用指纹浏览器 cookies 做登录态
CREATE TABLE IF NOT EXISTS accounts (
    handle TEXT PRIMARY KEY,
    email TEXT,
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
"""


def main():
    parser = argparse.ArgumentParser(description="Add one account to warmup.db")
    parser.add_argument("--db", default="warmup.db", help="path to warmup.db")
    parser.add_argument("--handle", required=True, help="X handle (no @)")
    parser.add_argument("--profile-id", required=True, help="fingerprint browser profile ID")
    parser.add_argument("--browser", default="adspower",
                        choices=["adspower", "bitbrowser", "manual", "patchright"],
                        help="fingerprint browser kind")
    parser.add_argument("--proxy", default="", help="proxy URL (optional)")
    parser.add_argument("--cookies", default="", help="path to cookies.json (optional)")
    parser.add_argument("--email", default="", help="account email (optional)")
    parser.add_argument("--notes", default="", help="notes field (optional)")
    parser.add_argument("--status", default="active",
                        choices=["active", "cooldown", "shadow_ban", "logged_out", "banned"],
                        help="initial status")
    args = parser.parse_args()

    handle = args.handle.lstrip("@")

    conn = sqlite3.connect(args.db)
    conn.executescript(SCHEMA_SQL)

    existing = conn.execute("SELECT handle FROM accounts WHERE handle = ?", (handle,)).fetchone()
    if existing:
        conn.execute(
            """UPDATE accounts
               SET fingerprint_profile_id = ?,
                   fingerprint_browser = ?,
                   proxy_url = COALESCE(NULLIF(?, ''), proxy_url),
                   cookies_path = COALESCE(NULLIF(?, ''), cookies_path),
                   email = COALESCE(NULLIF(?, ''), email),
                   notes = COALESCE(NULLIF(?, ''), notes),
                   status = ?
               WHERE handle = ?""",
            (
                args.profile_id, args.browser, args.proxy, args.cookies,
                args.email, args.notes, args.status, handle,
            ),
        )
        print(f"[updated] @{handle}")
    else:
        conn.execute(
            """INSERT INTO accounts
               (handle, fingerprint_profile_id, fingerprint_browser, proxy_url,
                cookies_path, email, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                handle, args.profile_id, args.browser, args.proxy,
                args.cookies, args.email, args.notes, args.status,
            ),
        )
        print(f"[inserted] @{handle}")

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM accounts WHERE status='active'").fetchone()[0]
    conn.close()

    print(f"[db] {total} total, {active} active")


if __name__ == "__main__":
    main()
