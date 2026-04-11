"""
gui/adspower.py · Fingerprint browser Local API wrapper

Supports both AdsPower and BitBrowser via a unified interface.
Detects which browser to use from the `browser_type` parameter.

AdsPower API: http://local.adspower.net:50325
  GET /api/v1/browser/start?user_id=X  → ws endpoint
  GET /api/v1/browser/stop?user_id=X

BitBrowser API: http://127.0.0.1:54345
  POST /browser/open/local  {"id": "X"}  → ws endpoint
  POST /browser/close       {"id": "X"}
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
# Unified browser client
# ============================================================================
class BrowserClient:
    """Unified client for AdsPower / BitBrowser / dry-run."""

    def __init__(self, base_url: str, browser_type: str = "adspower", dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.browser_type = browser_type.lower()  # "adspower" | "bitbrowser"
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
            raise RuntimeError(f"API error: {data}")
        return data

    def _post(self, path: str, json_body: dict) -> dict:
        if self.dry_run:
            return {"success": True, "data": {"ws": "ws://dry-run/fake"}}
        if requests is None:
            raise RuntimeError("requests not installed")
        r = requests.post(f"{self.base_url}{path}", json=json_body, timeout=20)
        r.raise_for_status()
        return r.json()

    # ---- high-level (auto-routes by browser_type) ----
    def start(self, profile_id: str) -> dict:
        """Start a browser profile. Returns dict with ws endpoint."""
        if self.dry_run:
            return {"ws": {"puppeteer": "ws://dry-run/fake"}}

        if self.browser_type == "bitbrowser":
            data = self._post("/browser/open/local", {"id": profile_id})
            if not data.get("success"):
                raise RuntimeError(f"BitBrowser open failed: {data}")
            return data.get("data", {})
        else:
            # AdsPower
            data = self._get("/api/v1/browser/start", {"user_id": profile_id, "open_tabs": 0})
            return data.get("data", {})

    def stop(self, profile_id: str) -> None:
        """Stop a browser profile. Best-effort, won't raise."""
        if self.dry_run:
            return
        try:
            if self.browser_type == "bitbrowser":
                self._post("/browser/close", {"id": profile_id})
            else:
                self._get("/api/v1/browser/stop", {"user_id": profile_id})
        except Exception:
            pass

    def get_ws_endpoint(self, start_result: dict) -> str:
        """Extract WebSocket endpoint from start() result."""
        if self.browser_type == "bitbrowser":
            # BitBrowser returns {"ws": "ws://127.0.0.1:XXXX/devtools/browser/..."}
            ws = start_result.get("ws", "")
            if ws:
                return ws
            # Fallback: some versions use nested structure
            return start_result.get("http", "")
        else:
            # AdsPower returns {"ws": {"puppeteer": "ws://..."}}
            ws = start_result.get("ws", {})
            if isinstance(ws, dict):
                return ws.get("puppeteer", "")
            return str(ws)

    def list_profiles(self) -> list[dict[str, Any]]:
        if self.dry_run:
            return [{"user_id": f"dry_{i:03d}", "name": f"dry_profile_{i}"} for i in range(3)]

        if self.browser_type == "bitbrowser":
            data = self._post("/browser/list", {"page": 0, "pageSize": 200})
            raw = data.get("data", {}).get("list", [])
            # Normalize to common format
            return [{"user_id": str(p.get("id", "")), "name": p.get("name", "")} for p in raw]
        else:
            data = self._get("/api/v1/user/list", {"page": 1, "page_size": 200})
            return data.get("data", {}).get("list", [])

    def ping(self) -> bool:
        if self.dry_run:
            return True
        try:
            if self.browser_type == "bitbrowser":
                data = self._post("/browser/list", {"page": 0, "pageSize": 1})
                return data.get("success", False)
            else:
                self._get("/api/v1/user/list", {"page": 1, "page_size": 1})
                return True
        except Exception:
            return False


# Backward compat alias
AdsPowerClient = BrowserClient


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
    ws_endpoint = client.get_ws_endpoint(info)
    if not ws_endpoint:
        raise RuntimeError(f"Browser didn't return ws endpoint: {info}")

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
