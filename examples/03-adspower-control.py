"""
Example 03 · AdsPower Local API Control
=======================================

通过 AdsPower Local API 启停指纹浏览器 profile，并用 Playwright 接管。

依赖：
    pip install requests playwright
    playwright install chromium

前置：
    1. 安装 AdsPower 桌面端 https://www.adspower.net/
    2. 设置 → API → 启动监听（默认 http://local.adspower.net:50325）
    3. 在 AdsPower 内手动创建 profile，记下 user_id

文档：https://github.com/AdsPower/localAPI
"""

import time
import requests
from playwright.sync_api import sync_playwright


ADSPOWER_API = "http://local.adspower.net:50325"


class AdsPower:
    def __init__(self, base_url: str = ADSPOWER_API):
        self.base_url = base_url

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = requests.get(f"{self.base_url}{path}", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"AdsPower error: {data}")
        return data.get("data", {})

    def _post(self, path: str, json_body: dict) -> dict:
        r = requests.post(f"{self.base_url}{path}", json=json_body, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"AdsPower error: {data}")
        return data.get("data", {})

    def list_profiles(self, page: int = 1, page_size: int = 100) -> list[dict]:
        data = self._get("/api/v1/user/list", {"page": page, "page_size": page_size})
        return data.get("list", [])

    def start(self, user_id: str, headless: bool = False) -> dict:
        """启动 profile，返回 selenium / puppeteer 接入点"""
        params = {
            "user_id": user_id,
            "open_tabs": 0,           # 不开默认 tab
            "headless": 1 if headless else 0,
        }
        return self._get("/api/v1/browser/start", params)

    def stop(self, user_id: str) -> dict:
        return self._get("/api/v1/browser/stop", {"user_id": user_id})

    def status(self, user_id: str) -> dict:
        return self._get("/api/v1/browser/active", {"user_id": user_id})

    def create_profile(
        self,
        name: str,
        proxy_host: str,
        proxy_port: str,
        proxy_user: str = "",
        proxy_pass: str = "",
        proxy_type: str = "http",
        group_id: str = "0",
    ) -> dict:
        body = {
            "name": name,
            "group_id": group_id,
            "user_proxy_config": {
                "proxy_soft": "other",
                "proxy_type": proxy_type,
                "proxy_host": proxy_host,
                "proxy_port": proxy_port,
                "proxy_user": proxy_user,
                "proxy_password": proxy_pass,
            },
            "fingerprint_config": {
                "automatic_timezone": "1",
                "language": ["en-US", "en"],
                "ua": "auto",
                "screen_resolution": "auto",
                "webrtc": "disabled",
            },
        }
        return self._post("/api/v1/user/create", body)


def open_x_with_adspower(user_id: str):
    """启动指定 profile，用 Playwright 接管，访问 X 主页。"""
    ads = AdsPower()

    info = ads.start(user_id)
    ws_endpoint = info["ws"]["puppeteer"]
    print(f"[+] profile started, ws: {ws_endpoint}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_endpoint)
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.new_page()

            page.goto("https://x.com/home")
            time.sleep(3)

            # 检查登录状态
            if "/i/flow/login" in page.url:
                print("[!] not logged in, please login manually first")
            else:
                print(f"[+] logged in, current url: {page.url}")
                page.screenshot(path=f"profile_{user_id}.png")
                print(f"[+] screenshot saved")

            time.sleep(5)
            page.close()
    finally:
        ads.stop(user_id)
        print(f"[+] profile stopped")


def main():
    ads = AdsPower()
    profiles = ads.list_profiles()
    print(f"[*] found {len(profiles)} profiles")
    for p in profiles[:5]:
        print(f"  {p['user_id']}  {p['name']}")

    if profiles:
        first = profiles[0]
        print(f"\n[*] opening first profile: {first['name']}")
        open_x_with_adspower(first["user_id"])


if __name__ == "__main__":
    main()
