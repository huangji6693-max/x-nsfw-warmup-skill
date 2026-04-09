#!/usr/bin/env python3
"""
X Warmup Skill · Live Prerequisites Checker

Run this before switching to live mode. Prints a colored pass/warn/fail report
for every component the warmup loop needs.

Exit code:
  0 = all critical checks passed (warnings OK)
  1 = at least one critical check failed

Usage:
    python scripts/check_prereqs.py
    python scripts/check_prereqs.py --json          # machine readable
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path


# ============================================================================
# Colors
# ============================================================================
IS_TTY = sys.stdout.isatty()
GREEN = "\033[92m" if IS_TTY else ""
RED = "\033[91m" if IS_TTY else ""
YELLOW = "\033[93m" if IS_TTY else ""
BLUE = "\033[94m" if IS_TTY else ""
BOLD = "\033[1m" if IS_TTY else ""
RESET = "\033[0m" if IS_TTY else ""


# ============================================================================
# Report state
# ============================================================================
report: list[dict] = []


def ok(category: str, msg: str, detail: str = ""):
    report.append({"category": category, "status": "ok", "msg": msg, "detail": detail})
    print(f"  {GREEN}✅{RESET} {msg}" + (f"  {detail}" if detail else ""))


def fail(category: str, msg: str, hint: str = ""):
    report.append({"category": category, "status": "fail", "msg": msg, "hint": hint})
    print(f"  {RED}❌{RESET} {msg}")
    if hint:
        print(f"       {YELLOW}→{RESET} {hint}")


def warn(category: str, msg: str, hint: str = ""):
    report.append({"category": category, "status": "warn", "msg": msg, "hint": hint})
    print(f"  {YELLOW}⚠️ {RESET} {msg}")
    if hint:
        print(f"       → {hint}")


def section(title: str):
    print(f"\n{BOLD}{BLUE}{title}{RESET}")
    print(f"{BLUE}{'─' * max(len(title), 30)}{RESET}")


# ============================================================================
# Checks
# ============================================================================
def check_python():
    section("Python")
    v = sys.version_info
    if v >= (3, 10):
        ok("python", f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        fail("python", f"Python {v.major}.{v.minor} is too old", "Need 3.10+")


def check_venv():
    section("Virtual environment")
    in_venv = sys.prefix != sys.base_prefix or hasattr(sys, "real_prefix")
    if in_venv:
        ok("venv", f"running in venv", sys.prefix)
    else:
        warn("venv", "not running in a venv",
             "Recommended: python -m venv .venv && source .venv/bin/activate")


def check_python_deps():
    section("Python dependencies")
    deps = [
        ("requests", "requests"),
        ("playwright", "playwright.sync_api"),
        ("nudenet", "nudenet"),
        ("twscrape", "twscrape"),
    ]
    for name, import_name in deps:
        try:
            __import__(import_name)
            ok("deps", name)
        except ImportError:
            fail("deps", f"{name} not installed", f"pip install {name}")
        except Exception as e:
            warn("deps", f"{name} imports but warns: {e}")


def check_playwright_browser():
    section("Playwright Chromium")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            exe = p.chromium.executable_path
            if exe and Path(exe).exists():
                ok("playwright", "Chromium installed", exe)
            else:
                fail("playwright", "Chromium binary not found",
                     "Run: playwright install chromium")
    except ImportError:
        fail("playwright", "playwright not installed", "pip install playwright")
    except Exception as e:
        warn("playwright", f"check failed: {e}",
             "Run: playwright install chromium")


def check_nudenet():
    section("NudeNet")
    try:
        from nudenet import NudeDetector
        d = NudeDetector()
        ok("nudenet", "model loaded successfully")
    except ImportError:
        fail("nudenet", "nudenet not installed", "pip install nudenet")
    except Exception as e:
        warn("nudenet", f"model load failed: {e}",
             "First run downloads the model (~80MB), check internet")


def check_adspower():
    section("AdsPower Local API")
    url = os.getenv("ADSPOWER_API", "http://local.adspower.net:50325")
    try:
        import requests
        r = requests.get(
            f"{url}/api/v1/user/list",
            params={"page": 1, "page_size": 100},
            timeout=5,
        )
        if r.status_code != 200:
            fail("adspower", f"HTTP {r.status_code} from {url}",
                 "Check AdsPower is running + Local API is enabled")
            return
        data = r.json()
        if data.get("code") != 0:
            fail("adspower", f"API error: {data.get('msg', 'unknown')}",
                 "Check AdsPower Local API version")
            return
        profiles = data.get("data", {}).get("list", [])
        ok("adspower", f"reachable at {url}", f"{len(profiles)} profile(s)")
        if len(profiles) == 0:
            warn("adspower", "0 profiles in AdsPower",
                 "Create profiles in AdsPower GUI first, then rerun onboard.py")
    except ImportError:
        warn("adspower", "requests not installed, can't check")
    except Exception as e:
        warn("adspower", f"can't reach {url}: {type(e).__name__}",
             "Skip if you use patchright / BitBrowser / other; "
             "otherwise start AdsPower and enable Settings → API → Local API")


def check_warmup_db():
    section("warmup.db")
    db_paths = [Path("warmup.db"), Path("data/warmup.db")]
    db_path = next((p for p in db_paths if p.exists()), None)

    if not db_path:
        fail("db", "warmup.db not found",
             "Run: python scripts/onboard.py   (to initialize + populate)")
        return

    ok("db", f"file exists", str(db_path))

    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = {r[0] for r in rows}

        required = ["accounts", "creators", "media_items", "follow_log"]
        for t in required:
            if t not in tables:
                fail("db", f"missing table: {t}",
                     "Run: python -c \"from examples.05_full_warmup_loop import init_schema; init_schema()\"")
                continue
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception as e:
                warn("db", f"{t}: can't count rows ({e})")
                continue

            if t == "accounts":
                if count == 0:
                    fail("db", f"{t}: 0 rows",
                         "Run: python scripts/onboard.py")
                else:
                    active = conn.execute(
                        "SELECT COUNT(*) FROM accounts WHERE status='active'"
                    ).fetchone()[0]
                    ok("db", f"{t}: {count} rows ({active} active)")
            elif t == "creators":
                if count == 0:
                    warn("db", f"{t}: 0 rows",
                         "Optional. Run scripts/seed_creators.py to populate.")
                else:
                    ok("db", f"{t}: {count} rows")
            elif t == "media_items":
                if count == 0:
                    warn("db", f"{t}: 0 rows",
                         "Optional. Run example 02 + gallery-dl to populate.")
                else:
                    ok("db", f"{t}: {count} rows")
            else:
                ok("db", f"{t}: {count} rows")

        conn.close()
    except Exception as e:
        fail("db", f"can't open warmup.db: {e}")


def check_env_file():
    section("Configuration (.env)")
    env_paths = [Path(".env"), Path("deploy/.env")]
    env_path = next((p for p in env_paths if p.exists()), None)

    if not env_path:
        warn("env", ".env not found",
             "cp deploy/.env.example .env   (optional; only needed for live mode + Telegram alerts)")
        return

    ok("env", f"found at {env_path}")
    content = env_path.read_text()
    mode = "dry-run"
    for line in content.splitlines():
        if line.startswith("WARMUP_MODE="):
            mode = line.split("=", 1)[1].strip()
            break

    if mode == "live":
        if "I_UNDERSTAND_THE_RISKS=yes" in content:
            warn("env", "LIVE mode is ENABLED",
                 "You're about to operate real X accounts. Double-check.")
        else:
            fail("env", "WARMUP_MODE=live but I_UNDERSTAND_THE_RISKS is not set",
                 "Set I_UNDERSTAND_THE_RISKS=yes in .env to confirm you accept the risks")
    else:
        ok("env", f"WARMUP_MODE={mode} (safe)")


def check_skill_files():
    section("Skill files")
    required = [
        "SKILL.md",
        "README.md",
        "tools-catalog.md",
        "AI-AGENT-PLAYBOOK.md",
        "requirements.txt",
        "examples/05-full-warmup-loop.py",
        "examples/02-nudenet-classify.py",
        "workflows/01-account-setup.md",
    ]
    missing = [f for f in required if not Path(f).exists()]
    if missing:
        fail("skill", f"{len(missing)} file(s) missing", ", ".join(missing))
    else:
        ok("skill", f"all {len(required)} required files present")


# ============================================================================
# Main
# ============================================================================
def summarize():
    passed = sum(1 for r in report if r["status"] == "ok")
    warned = sum(1 for r in report if r["status"] == "warn")
    failed = sum(1 for r in report if r["status"] == "fail")

    print()
    print(f"{BOLD}{'=' * 40}{RESET}")
    print(f"  {GREEN}passed{RESET}: {passed:>3}")
    print(f"  {YELLOW}warned{RESET}: {warned:>3}")
    print(f"  {RED}failed{RESET}: {failed:>3}")
    print(f"{BOLD}{'=' * 40}{RESET}")

    if failed == 0 and warned == 0:
        print(f"\n{GREEN}{BOLD}🎉 Ready to go live.{RESET}")
        return 0
    if failed == 0:
        print(f"\n{YELLOW}⚠️  Warnings only. You can run dry-run; address warnings before live.{RESET}")
        return 0
    print(f"\n{RED}{BOLD}❌ Fix the failed checks before going live.{RESET}")
    return 1


def main():
    parser = argparse.ArgumentParser(description="X Warmup Skill prereq checker")
    parser.add_argument("--json", action="store_true", help="emit JSON report instead")
    args = parser.parse_args()

    print(f"{BOLD}🦞 X Warmup Skill · Prerequisites Check{RESET}")
    print(f"{BOLD}{'=' * 40}{RESET}")

    check_python()
    check_venv()
    check_python_deps()
    check_playwright_browser()
    check_nudenet()
    check_adspower()
    check_skill_files()
    check_warmup_db()
    check_env_file()

    if args.json:
        print()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(0 if not any(r["status"] == "fail" for r in report) else 1)

    sys.exit(summarize())


if __name__ == "__main__":
    main()
