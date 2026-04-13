"""
gui/db.py · SQLite helpers

All GUI code goes through this module so we don't scatter raw SQL everywhere.
Schema is a superset of v0.4's warmup.db — adds a `settings` table for user
config and an `events` table for the live log stream.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


# ============================================================================
# Path + connection
# ============================================================================
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "warmup.db"

# Thread-local connection (NiceGUI runs tasks on different threads)
_tls = threading.local()


def get_db_path() -> Path:
    import os
    return Path(os.getenv("X_WARMUP_DB", str(DEFAULT_DB_PATH)))


def _conn() -> sqlite3.Connection:
    if not hasattr(_tls, "conn"):
        _tls.conn = sqlite3.connect(
            str(get_db_path()),
            check_same_thread=False,
            isolation_level=None,  # autocommit
        )
        _tls.conn.row_factory = sqlite3.Row
        _tls.conn.execute("PRAGMA journal_mode=WAL")
        _tls.conn.execute("PRAGMA synchronous=NORMAL")
    return _tls.conn


# ============================================================================
# Schema
# ============================================================================
SCHEMA_SQL = """
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

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    account TEXT,
    event_type TEXT NOT NULL,
    detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
"""


def init_schema() -> None:
    c = _conn()
    c.executescript(SCHEMA_SQL)


# ============================================================================
# Settings (key-value)
# ============================================================================
DEFAULT_SETTINGS = {
    "interval_min_hours": "4.0",
    "interval_max_hours": "8.0",
    "session_min_seconds": "120",
    "session_max_seconds": "300",
    "like_probability": "0.03",
    "max_concurrent": "1",
    "dry_run": "true",
    "browser_api": "http://127.0.0.1:54345",
    "browser_type": "bitbrowser",
    "running": "false",
}


def get_setting(key: str, default: str = "") -> str:
    row = _conn().execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    if row:
        return row["value"]
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]
    return default


def set_setting(key: str, value: str) -> None:
    _conn().execute(
        """INSERT INTO settings (key, value, updated_at)
           VALUES (?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                          updated_at = CURRENT_TIMESTAMP""",
        (key, value),
    )


def load_all_settings() -> dict[str, str]:
    result = dict(DEFAULT_SETTINGS)
    for row in _conn().execute("SELECT key, value FROM settings"):
        result[row["key"]] = row["value"]
    return result


def seed_default_settings() -> None:
    for k, v in DEFAULT_SETTINGS.items():
        existing = _conn().execute(
            "SELECT 1 FROM settings WHERE key = ?", (k,)
        ).fetchone()
        if not existing:
            _conn().execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)", (k, v)
            )


# ============================================================================
# Accounts
# ============================================================================
def list_accounts() -> list[dict[str, Any]]:
    rows = _conn().execute(
        """SELECT handle, fingerprint_profile_id, fingerprint_browser,
                  status, last_warmup_at, cooldown_until, notes
           FROM accounts ORDER BY handle"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_active_accounts() -> list[dict[str, Any]]:
    rows = _conn().execute(
        "SELECT * FROM accounts WHERE status = 'active' ORDER BY handle"
    ).fetchall()
    return [dict(r) for r in rows]


def pick_next_ready_account(interval_min_h: float, interval_max_h: float) -> dict[str, Any] | None:
    """Pick an active account that's ready to be warmed up again.

    Ready = (status='active') AND (last_warmup_at is NULL OR older than interval_min_h).
    Returns None if nothing ready.
    """
    import random
    cutoff = (datetime.utcnow() - timedelta(hours=interval_min_h)).isoformat()
    rows = _conn().execute(
        """SELECT * FROM accounts
           WHERE status = 'active'
             AND (last_warmup_at IS NULL OR last_warmup_at < ?)
           ORDER BY COALESCE(last_warmup_at, '1970') ASC""",
        (cutoff,),
    ).fetchall()
    if not rows:
        return None
    # Pick among the oldest few with some randomization to avoid fixed order
    pool = rows[: max(1, min(3, len(rows)))]
    return dict(random.choice(pool))


def update_account_status(handle: str, status: str, cooldown_hours: float = 0) -> None:
    c = _conn()
    if cooldown_hours > 0:
        cd = (datetime.utcnow() + timedelta(hours=cooldown_hours)).isoformat()
        c.execute(
            "UPDATE accounts SET status = ?, cooldown_until = ? WHERE handle = ?",
            (status, cd, handle),
        )
    else:
        c.execute(
            "UPDATE accounts SET status = ?, cooldown_until = NULL WHERE handle = ?",
            (status, handle),
        )


def mark_warmup_done(handle: str) -> None:
    _conn().execute(
        "UPDATE accounts SET last_warmup_at = CURRENT_TIMESTAMP WHERE handle = ?",
        (handle,),
    )


def upsert_account(
    handle: str,
    profile_id: str,
    browser: str = "adspower",
    proxy_url: str = "",
    status: str = "active",
    notes: str = "",
) -> bool:
    """Returns True if inserted, False if updated."""
    c = _conn()
    existing = c.execute(
        "SELECT 1 FROM accounts WHERE handle = ?", (handle,)
    ).fetchone()
    if existing:
        c.execute(
            """UPDATE accounts
               SET fingerprint_profile_id = ?, fingerprint_browser = ?,
                   proxy_url = ?, status = ?, notes = ?
               WHERE handle = ?""",
            (profile_id, browser, proxy_url, status, notes, handle),
        )
        return False
    c.execute(
        """INSERT INTO accounts
           (handle, fingerprint_profile_id, fingerprint_browser, proxy_url, status, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (handle, profile_id, browser, proxy_url, status, notes),
    )
    return True


def delete_account(handle: str) -> None:
    _conn().execute("DELETE FROM accounts WHERE handle = ?", (handle,))


def account_counts() -> dict[str, int]:
    rows = _conn().execute(
        "SELECT status, COUNT(*) AS n FROM accounts GROUP BY status"
    ).fetchall()
    total = _conn().execute("SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
    by_status = {r["status"]: r["n"] for r in rows}
    return {
        "total": total,
        "active": by_status.get("active", 0),
        "cooldown": by_status.get("cooldown", 0),
        "shadow_ban": by_status.get("shadow_ban", 0),
        "challenge": by_status.get("challenge", 0),
        "logged_out": by_status.get("logged_out", 0),
        "banned": by_status.get("banned", 0),
    }


# ============================================================================
# Events (live log)
# ============================================================================
def log_event(event_type: str, detail: str = "", account: str = "") -> None:
    _conn().execute(
        "INSERT INTO events (event_type, detail, account) VALUES (?, ?, ?)",
        (event_type, detail, account),
    )


def recent_events(limit: int = 100) -> list[dict[str, Any]]:
    rows = _conn().execute(
        "SELECT ts, event_type, detail, account FROM events ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def events_since(event_id: int, limit: int = 200) -> list[dict[str, Any]]:
    rows = _conn().execute(
        """SELECT id, ts, event_type, detail, account
           FROM events WHERE id > ? ORDER BY id ASC LIMIT ?""",
        (event_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def purge_old_events(keep_last: int = 5000) -> None:
    _conn().execute(
        """DELETE FROM events WHERE id NOT IN
           (SELECT id FROM events ORDER BY id DESC LIMIT ?)""",
        (keep_last,),
    )


# ============================================================================
# One-shot init (called on gui startup)
# ============================================================================
def bootstrap() -> None:
    init_schema()
    seed_default_settings()
