# Workflow 04 · Warmup Loop

> 把前三步的产出（账号池 + creator 池 + 媒体池 + 等级标签）串成**拟人化养号循环**。
> 直接基于 [CryptoBusher/Adspower-twitter-warmup](https://github.com/CryptoBusher/Adspower-twitter-warmup) 改造。

---

## 核心原则：随机度比代码量更重要

X 的 anti-bot 关注三件事：

1. **行为模式过于规律** —— 永远 9:00 / 12:00 / 18:00 发推 = bot 信号
2. **同一时间窗口内多账号同动作** —— 你的 IP / 指纹再好也保不住
3. **缺失"无意义"行为** —— 真人会刷 feed 不互动、会划掉、会停留

养号循环必须**主动生产噪声**，模拟真人 idle。

---

## 一次循环的行为预算

随机从下面池里抽 3-7 个动作，**乱序执行**：

| 动作 | 出现概率 | 单次耗时 | 备注 |
|---|---|---|---|
| 发推（带图） | 15% | 30-60s | 用 EXPLICIT / SUGGESTIVE 媒体 |
| 发推（纯文本） | 5% | 10-20s | 短文 / emoji / 链接 |
| 关注必关账号 | 10% | 5-10s / 个 | 商业目标 / VIP creator |
| 关注随机账号 | 20% | 5-10s / 个 | 从 creator 池抽 |
| 取关老账号 | 5% | 5-10s | 维持 follow 比例 |
| 刷 feed + 点赞 | 25% | 60-180s | 滚动 + 随机 like |
| 刷 feed + 转推 | 10% | 60-120s | 比 like 更"重" |
| 刷 feed + 关注作者 | 5% | 60-120s | 高质量来源沉淀 |
| 看个人主页 | 3% | 5-15s | 真人也会看自己 |
| 完全 idle | 2% | 30-300s | 划走 / 发呆 |

---

## 三层抖动

### 1. 坐标抖动

```python
import random

def jitter_click(page, selector):
    box = page.locator(selector).bounding_box()
    cx = box["x"] + box["width"] / 2 + random.uniform(-15, 15)
    cy = box["y"] + box["height"] / 2 + random.uniform(-10, 10)
    page.mouse.click(cx, cy)
```

### 2. 输入抖动

```python
def humanized_type(page, selector, text):
    page.locator(selector).click()
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.04, 0.18))
        if random.random() < 0.04:  # 4% 概率犹豫
            time.sleep(random.uniform(0.5, 1.5))
        if random.random() < 0.02:  # 2% 概率打错重打
            page.keyboard.press("Backspace")
            time.sleep(random.uniform(0.1, 0.3))
            page.keyboard.type(char)
```

### 3. 顺序抖动

```python
def warmup_account(account):
    actions = pick_random_actions(budget=random.randint(3, 7))
    random.shuffle(actions)
    for action in actions:
        action(account)
        # 动作之间也要 cooldown
        time.sleep(random.uniform(15, 90))
```

---

## 完整循环骨架

```python
import asyncio, random, time
from datetime import datetime, timedelta

async def warmup_loop(accounts):
    while True:
        # 从 active 账号中随机抽
        active = [a for a in accounts if a.status == "active" and 
                  (a.last_warmup_at is None or 
                   datetime.now() - a.last_warmup_at > timedelta(hours=random.uniform(2, 6)))]
        
        if not active:
            await asyncio.sleep(60)
            continue
        
        account = random.choice(active)
        try:
            await warmup_one(account)
            account.last_warmup_at = datetime.now()
        except ChallengeDetected:
            account.status = "cooldown"
            account.cooldown_until = datetime.now() + timedelta(hours=24)
        except ShadowBanDetected:
            account.status = "shadow_ban"
        except Exception as e:
            log_error(account, e)
        
        # 全局节流：每个号之间 30s - 5min 间隔
        await asyncio.sleep(random.uniform(30, 300))


async def warmup_one(account):
    # 1. 启动指纹浏览器
    profile = await adspower.start(account.fingerprint_profile_id)
    page = await connect_to_browser(profile.ws_endpoint)
    
    # 2. 健康检查
    await page.goto("https://x.com/home")
    if not await is_logged_in(page):
        raise NotLoggedIn(account)
    if await is_challenged(page):
        raise ChallengeDetected(account)
    
    # 3. 抽动作
    actions = pick_random_actions(budget=random.randint(3, 7))
    random.shuffle(actions)
    
    # 4. 顺序执行
    for action in actions:
        try:
            await action(page, account)
        except Exception as e:
            log_warning(f"Action {action.__name__} failed: {e}")
        # 截图归档
        await page.screenshot(path=f"logs/{account.handle}/{int(time.time())}.png")
        await asyncio.sleep(random.uniform(15, 90))
    
    # 5. 关闭浏览器
    await adspower.stop(account.fingerprint_profile_id)
```

---

## 关键动作实现

### 发推（带图）

```python
async def post_tweet_with_image(page, account):
    # 从媒体池抽一张：按等级分桶随机
    media = await pick_media(account, level=random.choice(["EXPLICIT", "SUGGESTIVE"]))
    caption = generate_caption(media)
    
    await page.goto("https://x.com/compose/post")
    await jitter_click(page, '[data-testid="tweetTextarea_0"]')
    await humanized_type(page, '[data-testid="tweetTextarea_0"]', caption)
    
    # 上传图
    await page.set_input_files('input[type="file"]', media.local_path)
    await asyncio.sleep(random.uniform(2, 5))  # 等上传
    
    # 如果是 hardcore，打 sensitive 标
    if media.content_level >= 2:
        await mark_sensitive(page)
    
    await jitter_click(page, '[data-testid="tweetButton"]')
    await asyncio.sleep(random.uniform(3, 8))
    
    media.posted_count += 1
```

### 刷 feed + 点赞

```python
async def scroll_and_like(page, account):
    await page.goto("https://x.com/home")
    duration = random.uniform(60, 180)
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # 随机滚动距离
        await page.mouse.wheel(0, random.randint(300, 800))
        await asyncio.sleep(random.uniform(1.5, 5))
        
        # 5-15% 概率点赞当前可见的随机一个推文
        if random.random() < 0.10:
            visible_tweets = page.locator('article[data-testid="tweet"]').all()
            if visible_tweets:
                tw = random.choice(visible_tweets)
                like_btn = tw.locator('[data-testid="like"]')
                if await like_btn.is_visible():
                    await jitter_click(page, like_btn)
                    await asyncio.sleep(random.uniform(0.5, 2))
```

### 关注随机 creator

```python
async def follow_random_creators(page, account, count=None):
    count = count or random.randint(1, 3)
    creators = await pick_creators(level="random", count=count)
    
    for c in creators:
        await page.goto(f"https://x.com/{c.handle}")
        await asyncio.sleep(random.uniform(2, 5))
        
        follow_btn = page.locator('[data-testid$="-follow"]')
        if await follow_btn.is_visible():
            await jitter_click(page, follow_btn)
            await asyncio.sleep(random.uniform(1, 3))
            
            # 50% 概率顺便看一眼对方主页再走
            if random.random() < 0.5:
                await page.mouse.wheel(0, random.randint(500, 1500))
                await asyncio.sleep(random.uniform(3, 10))
```

---

## 风控告警

```python
class ChallengeDetected(Exception): pass
class ShadowBanDetected(Exception): pass
class RateLimited(Exception): pass

async def detect_anomaly(page):
    # 1. challenge 弹窗
    if await page.locator("text=Verify your identity").count() > 0:
        raise ChallengeDetected()
    
    # 2. shadow ban：自己的推文搜不到自己
    test_query = f"from:{account.handle}"
    await page.goto(f"https://x.com/search?q={test_query}")
    if await page.locator("text=No results").count() > 0:
        raise ShadowBanDetected()
    
    # 3. rate limit
    if await page.locator("text=Rate limit exceeded").count() > 0:
        raise RateLimited()
```

---

## 多账号调度

```python
import asyncio
from asyncio import Semaphore

# 限制同时只能 N 个账号在跑（避免代理 / CPU 过载）
sem = Semaphore(3)

async def run_with_sem(account):
    async with sem:
        await warmup_one(account)

async def main(accounts):
    tasks = [run_with_sem(a) for a in accounts]
    await asyncio.gather(*tasks)
```

---

## ✅ 完成标志

- [ ] 至少 5 个号能完整跑一次循环
- [ ] 每次循环 3-7 个动作，乱序
- [ ] 三层抖动（坐标 + 输入 + 顺序）都接入
- [ ] 截图全部归档
- [ ] 风控告警接通 Telegram / 飞书

---

## 配套：跑半个月后的复盘

每周回看：

| 指标 | 目标 |
|---|---|
| 封号率 | < 5% / 周 |
| Shadow ban 率 | < 10% |
| 单号粉丝增长 | > 20 / 周 |
| 单条推文 impression | > 50 |
| 互动率 | > 2% |

发现某个动作组合或时段导致风险升高 → 立刻调整 `pick_random_actions` 的概率分布。

---

完整端到端 demo 见 [`examples/05-full-warmup-loop.py`](../examples/05-full-warmup-loop.py)。
