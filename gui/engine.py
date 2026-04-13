"""
gui/engine.py · Background scheduler + simplified actions

Simplified action set:
  - scroll_engage   scroll the home feed for a random duration,
                    use NudeNet to identify adult content before liking
  - idle            do nothing (true idle, models human noise)

NudeNet integration: when a tweet has media, screenshot the tweet element,
run NudeNet to detect if it's adult content. Only like if NSFW score exceeds
threshold. This builds the account's interest profile toward adult content.
"""

from __future__ import annotations

import asyncio
import logging
import random
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from . import db
from .adspower import BrowserClient, browser_session


# ============================================================================
# NudeNet lazy loader (only loads model once, on first use)
# ============================================================================
_nudenet_detector = None
_nudenet_available = None

NSFW_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_COVERED",
    "MALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
}

SUGGESTIVE_LABELS = {
    "FEMALE_BREAST_COVERED",
    "BUTTOCKS_COVERED",
    "BELLY_EXPOSED",
}


def _get_nudenet():
    """Lazy-load NudeNet detector. Returns None if not installed."""
    global _nudenet_detector, _nudenet_available
    if _nudenet_available is False:
        return None
    if _nudenet_detector is not None:
        return _nudenet_detector
    try:
        from nudenet import NudeDetector
        _nudenet_detector = NudeDetector()
        _nudenet_available = True
        log.info("NudeNet model loaded")
        return _nudenet_detector
    except ImportError:
        log.warning("nudenet not installed — liking without NSFW filter. pip install nudenet to enable.")
        _nudenet_available = False
        return None
    except Exception as e:
        log.warning(f"NudeNet init failed: {e}")
        _nudenet_available = False
        return None


async def is_nsfw_tweet(page, tweet_locator, threshold: float = 0.4) -> bool:
    """Screenshot a tweet element and check if it contains adult content via NudeNet.

    Returns True if adult content detected (should like), False otherwise (skip).
    If NudeNet is not available, returns True (fallback to like everything).
    """
    detector = _get_nudenet()
    if detector is None:
        return True  # no filter = like everything (backward compat)

    try:
        # Screenshot just this tweet to a temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name

        await tweet_locator.screenshot(path=tmp_path)

        # Run NudeNet in thread pool (it's CPU-bound)
        results = await asyncio.to_thread(detector.detect, tmp_path)

        # Clean up
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass

        # Check if any NSFW label exceeds threshold
        for r in results:
            if r["class"] in NSFW_LABELS and r["score"] >= threshold:
                return True
            if r["class"] in SUGGESTIVE_LABELS and r["score"] >= 0.6:
                return True

        return False
    except Exception as e:
        log.debug(f"NSFW check failed: {e}")
        return True  # on error, default to like (don't break the loop)


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
        # Support both old "adspower_api" key and new "browser_api" key
        self.adspower_api = settings.get("browser_api",
                            settings.get("adspower_api", "http://127.0.0.1:54345"))


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
    nsfw_skips = 0
    while time.time() < end:
        # scroll down by a humanized random amount
        await page.mouse.wheel(0, random.randint(300, 800))
        scrolls += 1

        # humanized pause — real humans don't scroll every 1.5s
        await asyncio.sleep(random.uniform(3.0, 8.0))

        # occasionally pause longer (simulate reading a tweet)
        if random.random() < 0.15:
            await asyncio.sleep(random.uniform(5.0, 15.0))

        # chance to evaluate a tweet for liking (3% default)
        if random.random() < settings.like_prob:
            try:
                tweets = await page.locator('article[data-testid="tweet"]').all()
                if tweets:
                    t = random.choice(tweets)
                    like = t.locator('[data-testid="like"]').first
                    if await like.is_visible():
                        # NudeNet check: only like if adult content detected
                        is_nsfw = await is_nsfw_tweet(page, t)
                        if is_nsfw:
                            await like.click()
                            likes += 1
                            await asyncio.sleep(random.uniform(2.0, 6.0))
                            db.log_event("like", f"@{account['handle']} liked NSFW tweet", account["handle"])
                        else:
                            nsfw_skips += 1
                            db.log_event("skip", f"@{account['handle']} skipped non-NSFW tweet", account["handle"])
                            await asyncio.sleep(random.uniform(1.0, 3.0))
            except Exception as e:
                log.debug(f"like attempt failed: {e}")

    return {"action": "scroll_engage", "scrolls": scrolls, "likes": likes, "skipped_non_nsfw": nsfw_skips, "duration_s": round(duration, 1)}


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
    browser_type = account.get("fingerprint_browser", "adspower")
    db.log_event("warmup_start", f"@{handle} ({'dry-run' if settings.dry_run else 'live'}) [{browser_type}]", handle)

    client = BrowserClient(settings.adspower_api, browser_type=browser_type, dry_run=settings.dry_run)

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

                # Global cadence: longer sleep between accounts to look human
                await asyncio.sleep(random.uniform(60, 300))

            db.log_event("scheduler_stop", "loop exited normally")
        except asyncio.CancelledError:
            db.log_event("scheduler_stop", "loop cancelled")
            raise
        except Exception as e:
            log.exception("scheduler crashed")
            db.log_event("scheduler_error", f"{type(e).__name__}: {e}")


# Module-level singleton
scheduler = Scheduler()
