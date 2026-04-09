#!/usr/bin/env python3
"""
Production entrypoint for X warmup loop.

This wrapper reads WARMUP_MODE from env and dispatches to dry-run or live.
It's used by systemd/docker-compose so those don't need to hardcode --dry-run vs --live.

Set env:
  WARMUP_MODE=dry-run   (default, safe)
  WARMUP_MODE=live      (real, requires all other env vars filled)

Also wires up:
  - Telegram alerts on exceptions (if TG_BOT_TOKEN set)
  - Auto retention cleanup for screenshots
  - Signal handling for graceful shutdown
"""

import asyncio
import logging
import os
import signal
import sys
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("x-warmup.runner")


# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------
_shutdown_requested = False


def _signal_handler(signum, frame):
    global _shutdown_requested
    log.info(f"received signal {signum}, starting graceful shutdown...")
    _shutdown_requested = True


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ---------------------------------------------------------------------------
# Telegram alerts
# ---------------------------------------------------------------------------
def send_telegram(message: str) -> None:
    token = os.getenv("TG_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TG_CHAT_ID", "").strip()
    if not token or not chat_id:
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": f"[x-warmup] {message}", "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        log.warning(f"failed to send telegram alert: {e}")


# ---------------------------------------------------------------------------
# Retention cleanup (screenshots + old logs)
# ---------------------------------------------------------------------------
def cleanup_old_screenshots():
    retention_days = int(os.getenv("SCREENSHOT_RETENTION_DAYS", "14"))
    cutoff = time.time() - retention_days * 86400
    shot_dir = Path("screenshots")
    if not shot_dir.exists():
        return
    removed = 0
    for f in shot_dir.rglob("*.png"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            pass
    if removed:
        log.info(f"cleaned {removed} old screenshots (> {retention_days}d)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    mode = os.getenv("WARMUP_MODE", "dry-run").strip().lower()
    log.info(f"starting x-warmup in mode={mode}")

    # 把仓库根目录加进 sys.path 以便 import examples
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

    # dry-run：跑一次 walkthrough 然后退出（systemd 会自动重启 = 持续 dry-run）
    if mode != "live":
        log.info("dry-run mode: no real API calls, no DB writes")
        try:
            from examples import __init__  # noqa
        except Exception:
            pass

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "warmup_loop",
            str(repo_root / "examples" / "05-full-warmup-loop.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.DRY_RUN = True

        try:
            asyncio.run(mod.dry_run_walkthrough())
        except Exception as e:
            log.error(f"dry-run walkthrough failed: {e}")
            traceback.print_exc()
            send_telegram(f"❌ dry-run walkthrough failed: `{e}`")
            sys.exit(1)

        log.info("dry-run complete. sleeping 10 min before next cycle.")
        for _ in range(600):
            if _shutdown_requested:
                return
            time.sleep(1)
        return

    # ------ live 模式 ------
    if os.getenv("I_UNDERSTAND_THE_RISKS", "").lower() != "yes":
        log.error(
            "LIVE mode refused: set env I_UNDERSTAND_THE_RISKS=yes to acknowledge "
            "that this violates X ToS and you accept full legal responsibility."
        )
        send_telegram("❌ live mode refused: I_UNDERSTAND_THE_RISKS not set")
        sys.exit(1)

    log.warning("LIVE mode enabled. Starting real warmup loop.")
    send_telegram("✅ x-warmup started in LIVE mode")

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "warmup_loop",
        str(repo_root / "examples" / "05-full-warmup-loop.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.DRY_RUN = False
    mod.init_schema()

    try:
        cleanup_old_screenshots()
        asyncio.run(mod.main_loop())
    except KeyboardInterrupt:
        log.info("graceful shutdown on KeyboardInterrupt")
        send_telegram("⚠️ x-warmup stopped (KeyboardInterrupt)")
    except Exception as e:
        log.error(f"live loop crashed: {e}")
        traceback.print_exc()
        send_telegram(f"🔥 x-warmup CRASHED: `{e}`")
        raise


if __name__ == "__main__":
    main()
