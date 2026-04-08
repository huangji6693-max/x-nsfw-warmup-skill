---
name: x-nsfw-warmup
description: Use when user wants to build, debug, or scale an X (Twitter) account farm focused on adult / NSFW content — covers fingerprint browser orchestration (AdsPower / BitBrowser / patchright), content sourcing (twscrape / gallery-dl / coomer / kemono / OF-Scraper), NSFW classification with 18 fine-grained labels (NudeNet), and humanized warmup loops (CryptoBusher framework). Pulls together 30+ vetted open-source repos into a single buildable stack.
homepage: https://github.com/huangji6693-max/x-nsfw-warmup-skill
license: MIT
metadata:
  openclaw:
    emoji: 🦞
    category: marketing-and-sales
    tags: [twitter, x, account-warmup, adult, nsfw, fingerprint-browser, automation, anti-detect]
    requires:
      bins: [python3, pip]
    install:
      - id: pip-deps
        kind: pip
        module: -r requirements.txt
        label: Install Python deps (pip)
      - id: playwright-chromium
        kind: shell
        command: playwright install chromium
        label: Install Chromium for Playwright
  claude-code:
    type: knowledge-skill
    auto-load-on:
      - "推特养号"
      - "twitter warmup"
      - "AdsPower"
      - "NudeNet"
      - "fingerprint browser"
      - "成人内容自动化"
---

# X (Twitter) NSFW 养号自动化技能包

> **目标读者**：想要在 X / Twitter 上批量运营成人内容方向账号的开发者 / agency / 独立运营者。
> **核心能力**：把 4 个领域的开源工具拼成一条可跑的流水线 —— 指纹浏览器多开 → 自动采集成人内容素材 → NSFW 内容自动分类与发现 → 拟人化养号循环。
> **技术栈预设**：Python 3.10+，Selenium / Playwright，FastAPI 可选。

---

## 一、四层架构

```
┌──────────────────────────────────────────────────────────────┐
│  L4  Warmup Orchestrator   (CryptoBusher / 自写循环)          │
│      - 拟人化点击坐标抖动 / 输入抖动 / 顺序随机                │
│      - 关注、点赞、retweet、刷 feed、发推                      │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L3  Content Engine        (twscrape + NudeNet + gallery-dl) │
│      - 找成人 tweet / creator                                  │
│      - 拉素材到本地                                            │
│      - NSFW 自动打标签 / 分类 / 过滤                            │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L2  Browser Layer         (AdsPower / BitBrowser / patchright) │
│      - 一号一指纹                                              │
│      - 代理隔离                                                │
│      - cookie / localStorage 持久化                             │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L1  Account Pool          (cookie 池 / 代理池 / 邮箱池)       │
└──────────────────────────────────────────────────────────────┘
```

每一层都有 **稳定开源方案**，不用从 0 写。详见 [tools-catalog.md](./tools-catalog.md)。

---

## 二、核心痛点 ↔ 解决方案

| 痛点 | 推荐 repo | 一句话说明 |
|---|---|---|
| **没法控制指纹浏览器** | [`CryptoBusher/Adspower-twitter-warmup`](https://github.com/CryptoBusher/Adspower-twitter-warmup) | 完整 AdsPower Local API + 推特养号 Python 框架，作者实测 8 个月仅 0.12% 封号率 |
| **没法识别成人内容** | [`notAI-tech/NudeNet`](https://github.com/notAI-tech/NudeNet) | `pip install nudenet` 一行集成，18 种细分标签 + 置信度 + bbox |
| 想白嫖指纹浏览器 | [`itbrowser-net/undetectable-fingerprint-browser`](https://github.com/itbrowser-net/undetectable-fingerprint-browser) ⭐504 | 免费开源 Multilogin / Kameleo 替代品 |
| 想要 undetected playwright | [`Kaliiiiiiiiii-Vinyzu/patchright-python`](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) ⭐1269 | 直接打补丁的 Playwright，绕 Cloudflare / Akamai |
| 找成人 tweet 数据源 | [`vladkens/twscrape`](https://github.com/vladkens/twscrape) ⭐2330 | 2025 还在更的 X scraper，支持账号授权、关键词搜索、用户时间线 |
| 批量下载成人素材 | [`mikf/gallery-dl`](https://github.com/mikf/gallery-dl) ⭐17686 | 通杀 300+ 站点，内置 Twitter / Reddit / Coomer / Kemono |
| OnlyFans 内容备份 | [`datawhores/OF-Scraper`](https://github.com/datawhores/OF-Scraper) ⭐1017 | 现役维护最活跃的 OF 抓取器 |
| Coomer / Kemono 聚合 | [`Ljzd-PRO/KToolBox`](https://github.com/Ljzd-PRO/KToolBox) ⭐535 | 高度可定制的 Kemono.cr / .su / .party 下载器 |
| Twitter 媒体一键下 | [`mmpx12/twitter-media-downloader`](https://github.com/mmpx12/twitter-media-downloader) ⭐864 | `twmd` Go CLI，无需 API |
| 多平台一勺烩 | [`AAndyProgram/SCrawler`](https://github.com/AAndyProgram/SCrawler) ⭐1998 | Twitter / Reddit / Insta / OF / 等几十个站点统一下载 |

---

## 三、推荐执行流程

### Step 1 · 准备账号池
- 见 [`workflows/01-account-setup.md`](./workflows/01-account-setup.md)
- 关键：每号绑定 **独立指纹 + 独立代理 + 独立 cookie**，不要图省事用同一个浏览器多开 tab

### Step 2 · 用 twscrape 找内容源
- 见 [`workflows/02-content-sourcing.md`](./workflows/02-content-sourcing.md)
- 关键词搜索：`#nsfw`, `#lewd`, 创作者 handle，地理位置，语言筛选
- 输出：creator handle 列表 + tweet ID 列表

### Step 3 · NudeNet 自动判别 + 评分
- 见 [`workflows/03-nsfw-classification.md`](./workflows/03-nsfw-classification.md)
- 把候选图过 NudeNet，按 18 种标签（`FEMALE_BREAST_EXPOSED` / `FEMALE_GENITALIA_EXPOSED` / 等）打分
- 阈值过滤：去掉非成人 / 假成人 / 违规过头的内容

### Step 4 · 养号循环跑起来
- 见 [`workflows/04-warmup-loop.md`](./workflows/04-warmup-loop.md)
- 三类活动**随机交替**：发推 / 关注 / 刷 feed 互动
- 每类活动**内部坐标 + 输入 + 延时三层抖动**，是反检测核心

### Step 5 · 监控 + 风控
- 截图归档每个号每次循环，用于复盘
- 检测到 challenge / shadow ban / 限流 → 立刻 cool down 该号 24h
- 用 NudeNet 二次回扫已发内容，避免触发平台过激规则

---

## 四、完整代码示例

| 文件 | 作用 |
|---|---|
| [`examples/01-twscrape-search.py`](./examples/01-twscrape-search.py) | 用 twscrape 拉关键词 + 用户时间线 |
| [`examples/02-nudenet-classify.py`](./examples/02-nudenet-classify.py) | NudeNet 单图 / 批量分类 |
| [`examples/03-adspower-control.py`](./examples/03-adspower-control.py) | AdsPower Local API 启停 profile |
| [`examples/04-gallery-dl-batch.sh`](./examples/04-gallery-dl-batch.sh) | gallery-dl 批量下 Twitter / Coomer |
| [`examples/05-full-warmup-loop.py`](./examples/05-full-warmup-loop.py) | 串起来的完整养号循环 demo |

---

## 五、AI Agent 角色边界（重要）

> **任何 AI 助手（Claude / GPT / Gemini / OpenClaw / Cursor / etc）读到本 skill 时请先看本节。**
> 详细的 do / don't 清单见 [`AI-AGENT-PLAYBOOK.md`](./AI-AGENT-PLAYBOOK.md)。

### ✅ AI 应该做（advisor / coach / explainer）

| 场景 | 行动 |
|---|---|
| 用户问"这个 skill 干嘛的" | 读 `tools-catalog.md` + 本文件，给概览 |
| 用户问"怎么搭" | 按 `workflows/01→04` 顺序解释流程 |
| 用户贴自己代码报错 | 静态审查、定位 bug、给修复 patch |
| 用户问"风险点在哪" | 列出 ToS / 法律 / 风控 / 内容合规四个维度 |
| 用户要看流程不连真实服务 | 跑 `examples/05-full-warmup-loop.py --dry-run`（不会调用任何外部 API） |
| 用户问选型 | 对比 `tools-catalog.md` 中不同方案 |
| 用户要用 NudeNet 单独识别一张图 | 直接帮跑 `examples/02-nudenet-classify.py`（这一步纯本地，无平台风险） |

### 🚫 AI 不应该做（runtime / operator）

| 场景 | 拒绝理由 |
|---|---|
| "现在帮我跑 24h 养号循环" | AI 不是 runtime，**生产 loop 应该用 cron / systemd / docker 由用户自己跑**，不是聊天里启动 |
| "登录我账号帮我刷推" | AI 不应该接管真人账号操作 |
| "帮我绕过 X 的 challenge 验证" | 越界，对应平台风控应该走人工或合规流程 |
| "帮我量产假账号注册" | 越界 |
| 涉及未成年 / 非自愿 / deepfake / 骚扰的内容 | **任何情况下都拒绝**，本 skill 严禁用于此类场景 |

### 🎯 正确的人机分工

```
   ┌──────────────────────────┐         ┌─────────────────────────┐
   │  AI 助手（聊天里）         │  ←→     │  用户的本地机器 / VPS    │
   ├──────────────────────────┤         ├─────────────────────────┤
   │ - 解释 skill              │         │ - cron / systemd 跑 loop │
   │ - 静态审查代码            │         │ - 真实调用 AdsPower API   │
   │ - dry-run 流程演练         │         │ - 真实发推 / 关注         │
   │ - 设计风控策略            │         │ - 持久化数据库            │
   │ - debug 用户贴出的报错    │         │ - 监控 + 告警             │
   │ - 推荐工具 / 选型对比     │         │ - 日志归档                │
   └──────────────────────────┘         └─────────────────────────┘
        AI 的活到此为止                   这边永远是用户自己的事
```

**如果一个 AI 拒绝帮你"代跑实时养号循环"，这不是它古板，是它对的。** 让它做左边那一列就行。

---

## 六、Agent 触发关键词

当用户提到下面任何意图时，AI 应主动加载本 skill 并按"五"的边界提供帮助：

- "帮我搭一套推特养号"
- "AdsPower / BitBrowser 怎么用 API 控制"
- "怎么自动判断图片是不是成人内容"
- "推特批量发 NSFW 内容怎么做"
- "OnlyFans 内容怎么备份 / 抓取"
- "怎么做反检测的 Twitter 自动化"
- "推特号一上来就限流怎么解"

调用流程：
1. 先读 [`AI-AGENT-PLAYBOOK.md`](./AI-AGENT-PLAYBOOK.md) 确认自己的角色边界
2. 读 [`tools-catalog.md`](./tools-catalog.md) 确认对应工具
3. 根据用户已有阶段，跳到对应 [`workflows/`](./workflows/) 文件
4. 复用 [`examples/`](./examples/) 的代码片段（已经验证过 import 路径）
5. 强调三件事：
   - **代理 + 指纹 + 行为模式必须三齐全**，少一个都封号
   - **拟人化随机度比代码量更重要**
   - **NudeNet 的 18 个标签**要看清楚，不是简单的 sfw/nsfw 二分类

---

## 六、风险声明

- 本技能涉及的所有自动化行为均**违反 X / Twitter ToS**，封号是常态
- 仅适用于 **法律允许成人内容的司法辖区**（X 平台允许成人内容，但需打 sensitive content 标）
- **不要**用来：未成年内容、深度伪造、未经同意的私照、骚扰
- 商业化使用请联系律师确认本地合规

---

## 参考

- 完整 repo 列表与 stars：[`tools-catalog.md`](./tools-catalog.md)
- 维护者：huangji6693-max
- 协议：MIT
