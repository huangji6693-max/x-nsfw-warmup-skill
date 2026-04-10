"""
gui/engine.py · Background scheduler + simplified actions

Simplified action set (vs examples/05-full-warmup-loop.py):
  - scroll_engage   scroll the home feed for a random duration,
                    occasionally like a visible tweet
  - idle            do nothing (true idle, models human "just opened and closed" behavior)

No posting, no following, no content sourcing. This is the "low-risk"
mode for users who just want their accounts to look alive without
making any outbound commitments.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Any

from . import db
from .adspower import AdsPowerClient, browser_session


log = logging.getLogger("x-warmup.engine")


# ============================================================================
# Settings snapshot
# ============================================================================
class EngineSettings:
    """Value-object snapshotted at each loop tick."""

    def __init__(self, settings: dict[str, str]):
        self.interval_min_h = float(settings.get("interval_min_hours", "2.0"))
        self.interval_max_h = float(settings.get("interval_max_hours", "6.0"))
        self.session_min_s = int(float(settings.get("session_min_seconds", "60")))
        self.session_max_s = int(float(settings.get("session_max_seconds", "180")))
        self.like_prob = float(settings.get("like_probability", "0.10"))
        self.max_concurrent = int(settings.get("max_concurrent", "1"))
        self.dry_run = settings.get("dry_run", "true").lower() == "true"
        self.adspower_api = settings.get("adspower_api", "http://local.adspower.net:50325")


def load_settings() -> EngineSettings:
    return EngineSettings(db.load_all_settings())


# ============================================================================
# Actions (simplified)
# ============================================================================
async def health_check(page) -> str:
    """Returns 'ok', 'challenge', 'shadow_ban', or 'logged_out'."""
    await page.goto("https://x.com/home")
    try:
        content = (await page.content()).lower()
    except Exception:
        content = ""

    url = getattr(page, "url", "")
    if isinstance(url, str) and "/i/flow/login" in url:
        return "logged_out"
    if "verify your identity" in content or "we need to make sure" in content:
        return "challenge"
    # Can't reliably detect shadow ban client-side, so treat as ok here
    return "ok"


async def action_scroll_engage(page, account: dict, settings: EngineSettings) -> dict:
    """Scroll the feed for a random duration; small chance to like visible tweets."""
    await page.goto("https://x.com/home")
    duration = random.uniform(settings.session_min_s, settings.session_max_s)
    end = time.time() + duration

    scrolls = 0
    likes = 0
    while time.time() < end:
        # scroll down by a humanized random amount
        await page.mouse.wheel(0, random.randint(300, 800))
        scrolls += 1

        # humanized pause
        await asyncio.sleep(random.uniform(1.5, 5.0))

        # small chance to like
        if random.random() < settings.like_prob:
            try:
                tweets = await page.locator('article[data-testid="tweet"]').all()
                if tweets:
                    t = random.choice(tweets)
                    like = t.locator('[data-testid="like"]').first
                    if await like.is_visible():
                        await like.click()
                        likes += 1
                        await asyncio.sleep(random.uniform(0.8, 2.5))
                        db.log_event("like", f"@{account['handle']} liked 1 tweet", account["handle"])
            except Exception as e:
                log.debug(f"like attempt failed: {e}")

    return {"action": "scroll_engage", "scrolls": scrolls, "likes": likes, "duration_s": round(duration, 1)}


async def action_idle(page, account: dict, settings: EngineSettings) -> dict:
    """Just sit on home page for a random idle duration. Models real human noise."""
    await page.goto("https://x.com/home")
    duration = random.uniform(settings.session_min_s / 2, settings.session_min_s)
    await asyncio.sleep(duration)
    return {"action": "idle", "duration_s": round(duration, 1)}


# Weight table — scroll dominates, idle is rare noise
ACTION_POOL = [
    (action_scroll_engage, 0.90),
    (action_idle, 0.10),
]


def pick_action():
    actions = [a for a, _ in ACTION_POOL]
    weights = [w for _, w in ACTION_POOL]
    return random.choices(actions, weights=weights, k=1)[0]


# ============================================================================
# One warmup cycle per account
# ============================================================================
async def warmup_one(account: dict, settings: EngineSettings) -> None:
    handle = account["handle"]
    db.log_event("warmup_start", f"@{handle} ({'dry-run' if settings.dry_run else 'live'})", handle)

    client = AdsPowerClient(settings.adspower_api, dry_run=settings.dry_run)

    try:
        async with browser_session(client, account["fingerprint_profile_id"]) as page:
            status = await health_check(page)
            if status != "ok":
                db.log_event(f"warmup_{status}", f"@{handle} → {status}", handle)
                if status == "challenge":
                    db.update_account_status(handle, "cooldown", cooldown_hours=24)
                elif status == "shadow_ban":
                    db.update_account_status(handle, "shadow_ban")
                elif status == "logged_out":
                    db.update_account_status(handle, "logged_out")
                return

            action = pick_action()
            result = await action(page, account, settings)
            db.mark_warmup_done(handle)
            db.log_event("warmup_done", f"@{handle} · {result}", handle)
    except Exception as e:
        log.exception("warmup failed")
        db.log_event("warmup_error", f"@{handle} · {type(e).__name__}: {e}", handle)


# ============================================================================
# Scheduler loop
# ============================================================================
class Scheduler:
    """Single-instance background scheduler. Polls DB every tick, picks an
    eligible account, runs one warmup cycle. Respects the 'running' setting
    flag so the UI can pause/resume."""

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._semaphore: asyncio.Semaphore | None = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running():
            return
        db.set_setting("running", "true")
        db.log_event("scheduler_start", "background loop started")
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        db.set_setting("running", "false")
        db.log_event("scheduler_stop", "background loop stopped")
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        try:
            while db.get_setting("running", "false").lower() == "true":
                settings = load_settings()

                if self._semaphore is None or self._semaphore._value != settings.max_concurrent:
                    self._semaphore = asyncio.Semaphore(settings.max_concurrent)

                account = db.pick_next_ready_account(
                    interval_min_h=settings.interval_min_h,
                    interval_max_h=settings.interval_max_h,
                )

                if account is None:
                    # Nothing ready — sleep a short time and re-check
                    await asyncio.sleep(30)
                    continue

                async with self._semaphore:
                    try:
                        await warmup_one(account, settings)
                    except Exception as e:
                        log.exception("warmup_one crashed")
                        db.log_event("error", f"warmup_one crash: {e}")

                # Global cadence: sleep between accounts to avoid rhythmic pattern
                await asyncio.sleep(random.uniform(30, 120))

            db.log_event("scheduler_stop", "loop exited normally")
        except asyncio.CancelledError:
            db.log_event("scheduler_stop", "loop cancelled")
            raise
        except Exception as e:
            log.exception("scheduler crashed")
            db.log_event("scheduler_error", f"{type(e).__name__}: {e}")


# Module-level singleton
scheduler = Scheduler()
