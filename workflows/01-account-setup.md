# Workflow 01 · Account Setup

> 准备好一个**可被 L4 自动化层调用**的账号池。这一步不做好，后面全白搭。

---

## 三件套：账号 + 代理 + 指纹

每一个号都必须严格 1:1:1 绑定：

```
账号 A ─── 代理 IP A ─── 指纹 profile A
账号 B ─── 代理 IP B ─── 指纹 profile B
...
```

**绝对不要**：
- 同一个 IP 跑多号（即使是不同号子段）
- 同一个浏览器开多 tab 登多号
- 复用上次跑过的 cookie / localStorage 串号

---

## Step 1 · 拿账号

### 选项 A · 买现成号
- **优点**：年龄老、有粉丝、avatar / banner 已设置好，开局就接近人号
- **缺点**：风险不可控，号商可能给二次销售号
- **推荐市场**：accfarm、accsmarket、bulkacc（自行评估，本仓库不背书）
- **价格区间**：0.1 ~ 5 USD / 个，按年龄 / 国家 / 是否带 email access 分级

### 选项 B · 自注册
- **必备**：临时邮箱 + 接码 + 代理
- **代码示例**：`examples/00-register-account.py`（待补，建议参考 [twscrape](https://github.com/vladkens/twscrape) 的 cookie auth 流程）
- **痛点**：X 注册风控很严，新号 7 天内 80% 概率秒封

### 选项 C · 跟号商定制
- **优点**：可指定国家 / 年龄 / 是否带邮箱
- **价格**：0.5 ~ 2 USD

---

## Step 2 · 配代理

### 代理类型对比

| 类型 | 价格 | 检测难度 | 适合 |
|---|---|---|---|
| 数据中心 IP | 0.1$ / 千次 | 容易识别 | 🚫 不推荐 |
| ISP / 静态住宅 | 1 ~ 3$ / IP / 月 | 中 | ⭐⭐⭐⭐ 主力 |
| 动态住宅（套餐） | 5 ~ 15$ / GB | 难 | ⭐⭐⭐ 流量型 |
| 4G/5G 移动 | 50+$ / 月 | 几乎不可识别 | ⭐⭐⭐⭐⭐ 高价值号 |

### 推荐供应商
- IPRoyal、Bright Data、Proxyseller（住宅 / ISP）
- airproxy.io（4G 移动）

### 验证代理质量
```bash
# 看 IP 是否被 X 标记
curl --proxy http://user:pass@host:port https://api.ipify.org
curl --proxy http://user:pass@host:port https://help.x.com/en  # 看是否拒绝访问
```

---

## Step 3 · 配指纹浏览器

### 方案 A · AdsPower（推荐入门）

1. 注册 https://www.adspower.net/，免费版送 5 个 profile
2. 导入号：用户名密码 + cookie + 代理
3. 启动 Local API：设置 → API → 启动监听 `http://local.adspower.net:50325`
4. 用 Python SDK 调用：

```python
from adspower import AdsPowerClient

client = AdsPowerClient()
profile = client.create_profile(
    name="x_account_001",
    proxy_config={
        "proxy_soft": "other",
        "proxy_type": "http",
        "proxy_host": "proxy.example.com",
        "proxy_port": "8080",
        "proxy_user": "user",
        "proxy_password": "pass"
    },
    fingerprint_config={
        "automatic_timezone": "1",
        "language": ["en-US", "en"],
        "ua": "auto",
        "screen_resolution": "auto"
    }
)
print("profile_id:", profile["user_id"])
```

完整代码见 [`examples/03-adspower-control.py`](../examples/03-adspower-control.py)。

### 方案 B · 白嫖 patchright + 自管指纹

```bash
pip install patchright
patchright install chromium
```

```python
from patchright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        proxy={"server": "http://proxy.example.com:8080", "username": "u", "password": "p"},
        headless=False,
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 ...",  # 从 Vinyzu/chrome-fingerprints 取一条
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
    )
    page = ctx.new_page()
    page.goto("https://x.com/")
```

⚠️ 注意：patchright 自动绕检测，但**不会改 canvas / WebGL 指纹**。需要配合 [Vinyzu/chrome-fingerprints](https://github.com/Vinyzu/chrome-fingerprints) 注入完整指纹包。

---

## Step 4 · 落地 cookie

第一次手动登录 → 导出 cookie → 存数据库：

```python
# 导出 cookie 到 json
cookies = ctx.cookies()
with open(f"cookies/{account_id}.json", "w") as f:
    json.dump(cookies, f)
```

下次启动直接注入：
```python
ctx.add_cookies(cookies)
page.goto("https://x.com/home")  # 应当无需登录
```

---

## Step 5 · 登记到账号池数据库

最简单的 schema（SQLite 也够）：

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    handle TEXT UNIQUE NOT NULL,
    email TEXT,
    password TEXT,
    cookies_path TEXT,
    proxy_url TEXT,
    fingerprint_profile_id TEXT,
    status TEXT DEFAULT 'active',  -- active / cooldown / banned
    last_warmup_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

后面所有 workflow 的输入都是 `accounts.status = 'active'`。

---

## Step 6 · 健康检查

每个号每天**必须**至少跑一次健康检查：

```python
def health_check(account):
    """登入后访问 /home，看是否被 challenge / shadow ban"""
    page.goto("https://x.com/home")
    if "verify your identity" in page.content().lower():
        return "challenge"
    if page.url.startswith("https://x.com/i/flow/login"):
        return "logged_out"
    if page.locator('[data-testid="primaryColumn"]').count() == 0:
        return "shadow_ban"
    return "ok"
```

挂了就立刻 `status = cooldown`，24h 内不再启动。

---

## ✅ 完成标志

- [ ] 至少 5 个号已入库
- [ ] 每个号有独立代理 + 独立指纹
- [ ] cookie 都能复用免登
- [ ] health_check 全绿
- [ ] 数据库 schema 建好

完成后进入 [02-content-sourcing.md](./02-content-sourcing.md)。
