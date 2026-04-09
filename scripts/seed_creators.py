#!/usr/bin/env python3
"""
X Warmup Skill · Seed Creators Table

Populate the creators table from a list of handles. This is what the warmup
loop pulls from when doing follow_random / follow_required actions.

This script does NOT download media — it only registers handles. To actually
fetch media for the media_items table, run example 02 (nudenet-classify) on
media you've downloaded via gallery-dl.

Usage:
    # From a file, one handle per line
    python scripts/seed_creators.py --from-file handles.txt

    # From stdin (paste + Ctrl-D)
    echo "alice_cute
    bob_xx
    carol_nsfw" | python scripts/seed_creators.py

    # Single handle from CLI
    python scripts/seed_creators.py --handle alice_cute --priority 9

    # Required creators (high priority, will be followed by follow_required action)
    python scripts/seed_creators.py --from-file vips.txt --priority 9

    # Random-pool creators (lower priority, used by follow_random action)
    python scripts/seed_creators.py --from-file pool.txt --priority 5

Input format (one handle per line):
    alice_cute
    @bob_xx            # @ is stripped
    carol_nsfw # notes  # anything after # is notes
    # this is a comment
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS creators (
    handle TEXT PRIMARY KEY,
    followers INTEGER,
    bio TEXT,
    nsfw_score REAL,
    follow_priority INTEGER DEFAULT 5,
    notes TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def parse_handle_line(line: str) -> tuple[str, str] | None:
    """Parse '@alice  # note' → ('alice', 'note') or None if comment/blank"""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    note = ""
    if "#" in line:
        handle_part, _, note = line.partition("#")
        note = note.strip()
        line = handle_part.strip()
    handle = line.lstrip("@").split()[0] if line else ""
    if not handle:
        return None
    return handle, note


def load_handles_from_source(args) -> list[tuple[str, str]]:
    handles: list[tuple[str, str]] = []

    if args.handle:
        handles.append((args.handle.lstrip("@"), ""))
        return handles

    if args.from_file:
        path = Path(args.from_file)
        if not path.exists():
            print(f"[error] file not found: {path}", file=sys.stderr)
            sys.exit(1)
        for line in path.read_text().splitlines():
            parsed = parse_handle_line(line)
            if parsed:
                handles.append(parsed)
        return handles

    # Read from stdin
    if not sys.stdin.isatty():
        for line in sys.stdin:
            parsed = parse_handle_line(line)
            if parsed:
                handles.append(parsed)
        return handles

    print("[error] no input. Use --handle, --from-file, or pipe via stdin.", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Seed creators table from a list of handles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--db", default="warmup.db", help="path to warmup.db")
    parser.add_argument("--handle", help="single handle to add")
    parser.add_argument("--from-file", help="file with one handle per line")
    parser.add_argument("--priority", type=int, default=5,
                        help="follow_priority 1-10 (default 5; use 8+ for required follows)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be inserted without writing")
    args = parser.parse_args()

    handles = load_handles_from_source(args)
    if not handles:
        print("[error] no valid handles to import", file=sys.stderr)
        sys.exit(1)

    print(f"[*] {len(handles)} handle(s) to process")
    print(f"[*] priority: {args.priority}")

    if args.dry_run:
        print("\n[dry-run] would insert:")
        for h, note in handles:
            print(f"  @{h}  {note}")
        print(f"\n[dry-run] total: {len(handles)}")
        return

    conn = sqlite3.connect(args.db)
    conn.executescript(SCHEMA_SQL)

    inserted = 0
    updated = 0
    for handle, note in handles:
        existing = conn.execute("SELECT handle FROM creators WHERE handle = ?", (handle,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE creators
                   SET follow_priority = ?,
                       notes = COALESCE(NULLIF(?, ''), notes)
                   WHERE handle = ?""",
                (args.priority, note, handle),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO creators (handle, follow_priority, notes) VALUES (?, ?, ?)""",
                (handle, args.priority, note),
            )
            inserted += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM creators").fetchone()[0]
    by_priority = conn.execute(
        "SELECT follow_priority, COUNT(*) FROM creators GROUP BY follow_priority ORDER BY follow_priority DESC"
    ).fetchall()
    conn.close()

    print(f"[ok] inserted {inserted}, updated {updated}")
    print(f"[db] total creators: {total}")
    print("[db] by priority:")
    for p, c in by_priority:
        tag = "required" if p >= 8 else "random-pool"
        print(f"       priority {p:>2}: {c:>4} ({tag})")


if __name__ == "__main__":
    main()
