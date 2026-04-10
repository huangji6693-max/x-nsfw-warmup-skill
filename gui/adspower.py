"""
gui/adspower.py · AdsPower Local API wrapper

Unified entry point for starting / stopping profiles. Supports a dry-run
mode where no real HTTP calls are made — for testing the GUI without a
running AdsPower desktop client.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore


# ============================================================================
# HTTP client (sync, wrapped via asyncio.to_thread for async contexts)
# ============================================================================
class AdsPowerClient:
    def __init__(self, base_url: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run

    # ---- low-level ----
    def _get(self, path: str, params: dict | None = None) -> dict:
        if self.dry_run:
            return {"code": 0, "data": {"ws": {"puppeteer": "ws://dry-run/fake"}}}
        if requests is None:
            raise RuntimeError("requests not installed")
        r = requests.get(f"{self.base_url}{path}", params=params or {}, timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"AdsPower error: {data}")
        return data

    # ---- high-level ----
    def list_profiles(self) -> list[dict[str, Any]]:
        if self.dry_run:
            return [
                {"user_id": f"dry_{i:03d}", "name": f"dry_profile_{i}"} for i in range(3)
            ]
        data = self._get("/api/v1/user/list", {"page": 1, "page_size": 200})
        return data.get("data", {}).get("list", [])

    def start(self, user_id: str) -> dict:
        data = self._get("/api/v1/browser/start", {"user_id": user_id, "open_tabs": 0})
        return data.get("data", {})

    def stop(self, user_id: str) -> None:
        try:
            self._get("/api/v1/browser/stop", {"user_id": user_id})
        except Exception:
            pass  # best-effort

    def ping(self) -> bool:
        """Returns True if AdsPower API is reachable."""
        if self.dry_run:
            return True
        try:
            self._get("/api/v1/user/list", {"page": 1, "page_size": 1})
            return True
        except Exception:
            return False


# ============================================================================
# Async session context
# ============================================================================
@asynccontextmanager
async def browser_session(client: AdsPowerClient, profile_id: str):
    """
    async with browser_session(client, profile_id) as page:
        await page.goto(...)

    In dry-run, yields a _DryPage that no-ops every call.
    Otherwise starts AdsPower profile + Playwright CDP connect + yields real page.
    """
    if client.dry_run:
        page = _DryPage()
        try:
            yield page
        finally:
            pass
        return

    info = await asyncio.to_thread(client.start, profile_id)
    ws_endpoint = info.get("ws", {}).get("puppeteer")
    if not ws_endpoint:
        raise RuntimeError(f"AdsPower didn't return ws endpoint: {info}")

    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise RuntimeError("playwright not installed") from e

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            yield page
        finally:
            await asyncio.to_thread(client.stop, profile_id)


# ============================================================================
# Dry-run page stub (matches Playwright Page surface we actually use)
# ============================================================================
class _DryPage:
    url = "https://x.com/home"

    async def goto(self, url: str, **kw):
        await asyncio.sleep(0)

    async def content(self) -> str:
        return ""

    async def wait_for_load_state(self, *a, **kw):
        await asyncio.sleep(0)

    async def screenshot(self, **kw):
        await asyncio.sleep(0)

    def locator(self, sel: str):
        return _DryLocator()

    @property
    def mouse(self):
        return _DryMouse()

    @property
    def keyboard(self):
        return _DryKeyboard()


class _DryLocator:
    @property
    def first(self):
        return self

    async def all(self):
        return [self, self, self]

    async def count(self) -> int:
        return 1

    async def is_visible(self) -> bool:
        return True

    async def click(self, **kw):
        await asyncio.sleep(0)

    def locator(self, sel: str):
        return self

    async def bounding_box(self):
        return {"x": 100, "y": 100, "width": 50, "height": 30}


class _DryMouse:
    async def wheel(self, *a, **kw):
        await asyncio.sleep(0)

    async def click(self, *a, **kw):
        await asyncio.sleep(0)

    async def move(self, *a, **kw):
        await asyncio.sleep(0)


class _DryKeyboard:
    async def type(self, *a, **kw):
        await asyncio.sleep(0)

    async def press(self, *a, **kw):
        await asyncio.sleep(0)
