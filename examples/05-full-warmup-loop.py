"""
Example 05 · Full Warmup Loop (Demo)
====================================

把前 4 步的产出（账号池 + creator 池 + 媒体池 + 等级标签）串成一条**完整的拟人化养号循环**。

这是一个 demo 骨架，**不能直接 production 用**，但所有关键组件已就位：
- AdsPower 启停
- Playwright 接管 + 三层抖动
- 5 类拟人化动作（发推 / 关注必关 / 关注随机 / 刷 feed 点赞 / 完全 idle）
- 风控告警 + 自动 cool down
- 截图归档

模式
----
- **dry-run**（默认 + 推荐 AI 助手用）：
    `python 05-full-warmup-loop.py --dry-run`
    完全不连 AdsPower、不连 X、不连数据库、不发任何请求；
    只在终端打印每一步会做什么，可以让人 / AI 看清流程结构。
- **live**：
    `python 05-full-warmup-loop.py --live`
    真实跑。要求用户已经自己装好 AdsPower、配好 profile、填好账号池数据库。
    AI 助手不应在聊天里启动 live 模式 —— 应由用户自己 cron / systemd 调度。

依赖：
    pip install requests playwright nudenet
    playwright install chromium

参考主框架：https://github.com/CryptoBusher/Adspower-twitter-warmup
"""

import argparse
import asyncio
import json
import random
import sqlite3
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path

# 重 import 在 dry-run 模式下不强制要求，避免 AI 助手在聊天里 walk-through 时缺包失败
try:
    import requests
except ImportError:
    requests = None

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    async_playwright = None
    Page = None  # type: ignore


# ========== 配置 ==========
ADSPOWER_API = "http://local.adspower.net:50325"
DB_PATH = "warmup.db"
LOG_DIR = Path("logs")

# dry-run 模式全局开关，main 里根据 argparse 设置
DRY_RUN = False


def dry(msg: str) -> None:
    """dry-run 模式下的统一前缀日志"""
    print(f"[DRY] {msg}")


# ========== 异常 ==========
class ChallengeDetected(Exception):
    pass


class ShadowBanDetected(Exception):
    pass


class NotLoggedIn(Exception):
    pass


# ========== AdsPower ==========
def adspower_start(user_id: str) -> dict:
    if DRY_RUN:
        dry(f"adspower_start({user_id}) → 不会真实启动浏览器")
        return {"ws": {"puppeteer": "ws://dry-run/fake-endpoint"}}
    r = requests.get(f"{ADSPOWER_API}/api/v1/browser/start", params={"user_id": user_id, "open_tabs": 0}, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def adspower_stop(user_id: str) -> None:
    if DRY_RUN:
        dry(f"adspower_stop({user_id}) → 不会真实关闭")
        return
    requests.get(f"{ADSPOWER_API}/api/v1/browser/stop", params={"user_id": user_id}, timeout=30)


class _DryPage:
    """dry-run 模式下的假 Page，吞掉所有方法调用"""
    url = "https://x.com/home"

    async def goto(self, url, **kw):
        dry(f"page.goto({url})")

    async def content(self):
        return ""

    async def screenshot(self, path: str, **kw):
        dry(f"page.screenshot({path})")

    def locator(self, sel):
        return self

    def first(self):  # noqa
        return self

    async def is_visible(self):
        return True

    async def click(self, **kw):
        dry("page.click()")

    async def all(self):
        return []

    async def count(self):
        return 1

    async def bounding_box(self):
        return {"x": 100, "y": 100, "width": 50, "height": 30}

    @property
    def mouse(self):
        return self

    async def wheel(self, *a, **kw):
        dry(f"page.mouse.wheel{a}")

    @property
    def keyboard(self):
        return self

    async def type(self, *a, **kw):
        pass

    async def press(self, key):
        pass


@asynccontextmanager
async def adspower_session(user_id: str):
    info = adspower_start(user_id)
    if DRY_RUN:
        try:
            yield _DryPage()
        finally:
            adspower_stop(user_id)
        return

    ws_endpoint = info["ws"]["puppeteer"]
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            yield page
    finally:
        adspower_stop(user_id)


# ========== 三层抖动 ==========
async def jitter_click(page: Page, selector: str):
    el = page.locator(selector)
    box = await el.bounding_box()
    if not box:
        await el.click()
        return
    cx = box["x"] + box["width"] / 2 + random.uniform(-15, 15)
    cy = box["y"] + box["height"] / 2 + random.uniform(-10, 10)
    await page.mouse.click(cx, cy)


async def humanized_type(page: Page, selector: str, text: str):
    await page.locator(selector).click()
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.04, 0.18))
        if random.random() < 0.04:
            await asyncio.sleep(random.uniform(0.5, 1.5))
        if random.random() < 0.02:
            await page.keyboard.press("Backspace")
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await page.keyboard.type(char)


# ========== 风控检测 ==========
async def health_check(page: Page) -> str:
    await page.goto("https://x.com/home")
    await asyncio.sleep(random.uniform(2, 5))
    if "/i/flow/login" in page.url:
        return "logged_out"
    content = (await page.content()).lower()
    if "verify your identity" in content or "we need to make sure" in content:
        return "challenge"
    if await page.locator('[data-testid="primaryColumn"]').count() == 0:
        return "shadow_ban"
    return "ok"


# ========== 5 类拟人化动作 ==========
async def action_post_tweet(page: Page, account: dict, db: sqlite3.Connection):
    """从媒体池抽一张图发推"""
    cur = db.execute(
        "SELECT id, local_path FROM media_items WHERE content_level >= 1 AND posted_count = 0 ORDER BY RANDOM() LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        print(f"  [{account['handle']}] no media available, skip post")
        return
    media_id, media_path = row
    caption = random.choice([
        "Late night vibes 🌙", "Mood today ✨", "Just saying hi", "Feeling cute ✨",
        "Hello world", "Vibes only", "What do you think?", "DMs open 💌",
    ])

    await page.goto("https://x.com/compose/post")
    await asyncio.sleep(random.uniform(2, 4))
    await humanized_type(page, '[data-testid="tweetTextarea_0"]', caption)
    await asyncio.sleep(random.uniform(1, 3))

    file_input = page.locator('input[type="file"]').first
    await file_input.set_input_files(media_path)
    await asyncio.sleep(random.uniform(3, 7))

    await jitter_click(page, '[data-testid="tweetButton"]')
    await asyncio.sleep(random.uniform(3, 8))

    db.execute("UPDATE media_items SET posted_count = posted_count + 1 WHERE id = ?", (media_id,))
    db.commit()
    print(f"  [{account['handle']}] posted tweet with media {media_id}")


async def action_follow_required(page: Page, account: dict, db: sqlite3.Connection):
    cur = db.execute(
        "SELECT handle FROM creators WHERE follow_priority >= 8 AND handle NOT IN (SELECT target_handle FROM follow_log WHERE account = ?) ORDER BY RANDOM() LIMIT 1",
        (account["handle"],),
    )
    row = cur.fetchone()
    if not row:
        return
    target = row[0]
    await page.goto(f"https://x.com/{target}")
    await asyncio.sleep(random.uniform(3, 7))
    follow_btn = page.locator('[data-testid$="-follow"]').first
    if await follow_btn.is_visible():
        await jitter_click(page, '[data-testid$="-follow"]')
        await asyncio.sleep(random.uniform(1, 3))
        db.execute("INSERT INTO follow_log (account, target_handle) VALUES (?, ?)", (account["handle"], target))
        db.commit()
        print(f"  [{account['handle']}] followed (required) @{target}")


async def action_follow_random(page: Page, account: dict, db: sqlite3.Connection):
    n = random.randint(1, 3)
    cur = db.execute(
        "SELECT handle FROM creators WHERE follow_priority < 8 AND handle NOT IN (SELECT target_handle FROM follow_log WHERE account = ?) ORDER BY RANDOM() LIMIT ?",
        (account["handle"], n),
    )
    targets = [r[0] for r in cur.fetchall()]
    for target in targets:
        await page.goto(f"https://x.com/{target}")
        await asyncio.sleep(random.uniform(2, 5))
        follow_btn = page.locator('[data-testid$="-follow"]').first
        if await follow_btn.is_visible():
            await jitter_click(page, '[data-testid$="-follow"]')
            await asyncio.sleep(random.uniform(1, 3))
            db.execute("INSERT INTO follow_log (account, target_handle) VALUES (?, ?)", (account["handle"], target))
            db.commit()
            print(f"  [{account['handle']}] followed (random) @{target}")
        # 50% 概率看一眼对方主页
        if random.random() < 0.5:
            await page.mouse.wheel(0, random.randint(500, 1500))
            await asyncio.sleep(random.uniform(3, 10))


async def action_scroll_and_engage(page: Page, account: dict, db: sqlite3.Connection):
    await page.goto("https://x.com/home")
    duration = random.uniform(60, 180)
    end = time.time() + duration
    while time.time() < end:
        await page.mouse.wheel(0, random.randint(300, 800))
        await asyncio.sleep(random.uniform(1.5, 5))
        if random.random() < 0.10:
            tweets = await page.locator('article[data-testid="tweet"]').all()
            if tweets:
                t = random.choice(tweets)
                like = t.locator('[data-testid="like"]').first
                try:
                    if await like.is_visible():
                        await like.click()
                        await asyncio.sleep(random.uniform(0.5, 2))
                        print(f"  [{account['handle']}] liked a tweet")
                except Exception:
                    pass


async def action_idle(page: Page, account: dict, db: sqlite3.Connection):
    duration = random.uniform(30, 300)
    print(f"  [{account['handle']}] idling for {duration:.0f}s")
    await asyncio.sleep(duration)


ACTIONS = {
    "post_tweet": (action_post_tweet, 0.20),
    "follow_required": (action_follow_required, 0.10),
    "follow_random": (action_follow_random, 0.20),
    "scroll_engage": (action_scroll_and_engage, 0.45),
    "idle": (action_idle, 0.05),
}


def pick_actions(budget: int) -> list:
    names = list(ACTIONS.keys())
    weights = [ACTIONS[n][1] for n in names]
    chosen = random.choices(names, weights=weights, k=budget)
    random.shuffle(chosen)
    return [(n, ACTIONS[n][0]) for n in chosen]


# ========== 主循环 ==========
async def warmup_one(account: dict, db: sqlite3.Connection):
    print(f"\n[*] warming up @{account['handle']}")
    async with adspower_session(account["fingerprint_profile_id"]) as page:
        status = await health_check(page)
        if status == "challenge":
            raise ChallengeDetected(account["handle"])
        if status == "shadow_ban":
            raise ShadowBanDetected(account["handle"])
        if status == "logged_out":
            raise NotLoggedIn(account["handle"])

        budget = random.randint(3, 7)
        actions = pick_actions(budget)
        print(f"  budget={budget} actions={[n for n, _ in actions]}")

        for name, fn in actions:
            try:
                await fn(page, account, db)
            except Exception as e:
                print(f"  [{account['handle']}] action {name} failed: {e}")
            ts = int(time.time())
            shot_dir = LOG_DIR / account["handle"]
            if not DRY_RUN:
                shot_dir.mkdir(parents=True, exist_ok=True)
            try:
                await page.screenshot(path=str(shot_dir / f"{ts}_{name}.png"))
            except Exception:
                pass
            sleep_s = 0 if DRY_RUN else random.uniform(15, 90)
            await asyncio.sleep(sleep_s)


async def main_loop(db_path: str = DB_PATH, max_concurrent: int = 3):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    sem = asyncio.Semaphore(max_concurrent)

    while True:
        cur = db.execute(
            "SELECT * FROM accounts WHERE status = 'active' AND (last_warmup_at IS NULL OR last_warmup_at < ?)",
            ((datetime.now() - timedelta(hours=random.uniform(2, 6))).isoformat(),),
        )
        accounts = [dict(r) for r in cur.fetchall()]
        if not accounts:
            print("[-] no accounts ready, sleeping 60s")
            await asyncio.sleep(60)
            continue

        random.shuffle(accounts)

        async def run(acc):
            async with sem:
                try:
                    await warmup_one(acc, db)
                    db.execute("UPDATE accounts SET last_warmup_at = ? WHERE handle = ?", (datetime.now().isoformat(), acc["handle"]))
                    db.commit()
                except ChallengeDetected:
                    cooldown = (datetime.now() + timedelta(hours=24)).isoformat()
                    db.execute("UPDATE accounts SET status='cooldown', cooldown_until=? WHERE handle=?", (cooldown, acc["handle"]))
                    db.commit()
                    print(f"  [!] @{acc['handle']} → challenge, cooldown 24h")
                except ShadowBanDetected:
                    db.execute("UPDATE accounts SET status='shadow_ban' WHERE handle=?", (acc["handle"],))
                    db.commit()
                    print(f"  [!] @{acc['handle']} → shadow ban")
                except NotLoggedIn:
                    db.execute("UPDATE accounts SET status='logged_out' WHERE handle=?", (acc["handle"],))
                    db.commit()
                    print(f"  [!] @{acc['handle']} → logged out")
                except Exception as e:
                    print(f"  [!] @{acc['handle']} unexpected error: {e}")

        await asyncio.gather(*(run(a) for a in accounts[:max_concurrent]))
        await asyncio.sleep(random.uniform(30, 300))


def init_schema(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            handle TEXT PRIMARY KEY,
            email TEXT,
            password TEXT,
            cookies_path TEXT,
            proxy_url TEXT,
            fingerprint_profile_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            cooldown_until TIMESTAMP,
            last_warmup_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS creators (
            handle TEXT PRIMARY KEY,
            followers INTEGER,
            bio TEXT,
            nsfw_score REAL,
            follow_priority INTEGER DEFAULT 5
        );
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_path TEXT UNIQUE,
            content_level INTEGER,
            nsfw_labels TEXT,
            posted_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS follow_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            target_handle TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


async def dry_run_walkthrough():
    """干跑：演示一次完整的循环逻辑，不连任何外部服务，不写数据库"""
    print("=" * 60)
    print("DRY RUN · X warmup loop walkthrough")
    print("=" * 60)
    print("Mode: NO real API calls · NO real DB writes · NO real X actions")
    print()

    fake_account = {
        "handle": "demo_user_001",
        "fingerprint_profile_id": "ads_fake_001",
        "status": "active",
    }
    fake_db = type("FakeDB", (), {
        "execute": lambda self, *a, **k: type("Cur", (), {"fetchone": lambda s: None, "fetchall": lambda s: []})(),
        "commit": lambda self: None,
    })()

    try:
        await warmup_one(fake_account, fake_db)
    except Exception as e:
        dry(f"walkthrough caught: {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("DRY RUN done. To run for real (NOT recommended via AI chat):")
    print("  python 05-full-warmup-loop.py --live")
    print("And only after you have:")
    print("  1) AdsPower running locally with profiles configured")
    print("  2) accounts table populated in warmup.db")
    print("  3) media_items table populated (run example 02 first)")
    print("  4) creators table populated (run example 01 first)")
    print("  5) Reviewed and accepted the legal/ToS risks in LICENSE")
    print("=" * 60)


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser(
        description="X warmup loop demo (DRY RUN by default)",
        epilog="AI assistants: please use --dry-run only. Real execution is the user's responsibility.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True,
                      help="(default) walk through the loop with NO real API calls / DB writes")
    mode.add_argument("--live", action="store_true",
                      help="actually run against AdsPower + X. User responsibility, NOT for AI chat sessions.")
    args = parser.parse_args()

    if args.live:
        DRY_RUN = False
        confirm = input(
            "\n⚠️  LIVE MODE\n"
            "This will start AdsPower profiles and perform real X.com actions.\n"
            "This violates X ToS and may get accounts banned.\n"
            "Type 'I understand' to continue: "
        )
        if confirm.strip() != "I understand":
            print("Aborted.")
            sys.exit(1)
        init_schema()
        print("[+] schema ready. starting real warmup loop...")
        asyncio.run(main_loop())
    else:
        DRY_RUN = True
        asyncio.run(dry_run_walkthrough())


if __name__ == "__main__":
    main()
