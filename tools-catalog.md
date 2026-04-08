# Tools Catalog

> 完整开源工具目录，按四层架构分类。每个 repo 都来自 GitHub stars > 50 的实际可用项目。

---

## L1 · Account Pool（账号池）

养号的最底层是账号本身。这部分**没有银弹开源方案**，需要自建：

| 来源 | 推荐策略 |
|---|---|
| **付费号商** | 0.1 ~ 0.5 USD / 个，年龄越久越贵；越南、菲律宾、印尼、俄罗斯号最便宜 |
| **自注册** | 用接码平台（sms-activate、5sim）+ 临时邮箱（mail.tm、tempmail.plus），每号配独立代理 |
| **代理池** | 911s5（已倒）→ IPRoyal / Bright Data / Proxyseller 住宅代理，**必须每号独立 IP** |
| **邮箱池** | outlook 子号、临时邮箱、自购域名 catch-all |

⚠️ 注意：本仓库不提供账号 / 代理 / 邮箱购买建议，自行评估合规与风险。

---

## L2 · Browser Layer（指纹浏览器）

### 商业指纹浏览器（API 控制）

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`AdsPower/localAPI`](https://github.com/AdsPower/localAPI) | 107 | JS | AdsPower 官方 Local API 文档 + 示例。`POST /api/v1/browser/start?user_id=xxx` 启动 profile，返回 selenium / puppeteer endpoint |
| [`CrocoFactory/adspower`](https://github.com/CrocoFactory/adspower) | 56 | Python | 现代化的 AdsPower Python SDK，封装好 profile CRUD + 启停 |
| [`16627517673/bitbrowser-automation`](https://github.com/16627517673/bitbrowser-automation) | 62 | Python | BitBrowser 全套自动化（FastAPI + Vue 后台），含批量任务调度 |
| [`CloakHQ/CloakBrowser-Manager`](https://github.com/CloakHQ/CloakBrowser-Manager) | 76 | Python | CloakBrowser 的 Web profile 管理面板 |

### 开源指纹浏览器（白嫖方案）

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`itbrowser-net/undetectable-fingerprint-browser`](https://github.com/itbrowser-net/undetectable-fingerprint-browser) | 504 | - | **免费开源 Multilogin / Incogniton / Kameleo 替代品**，主打白嫖 |
| [`botswin/BotBrowser`](https://github.com/botswin/BotBrowser) | 2319 | TS | Advanced Privacy Browser Core，自带统一指纹防御绕过 Cloudflare / Akamai |
| [`bablosoft/puppeteer-with-fingerprints`](https://github.com/bablosoft/puppeteer-with-fingerprints) | 450 | JS | Puppeteer + 指纹替换库 |
| [`bablosoft/playwright-with-fingerprints`](https://github.com/bablosoft/playwright-with-fingerprints) | 321 | JS | Playwright + 指纹替换库 |

### Undetected 浏览器自动化（不要指纹浏览器，直接打补丁）

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`Kaliiiiiiiiii-Vinyzu/patchright`](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) | 2835 | TS | undetected 版 Playwright |
| [`Kaliiiiiiiiii-Vinyzu/patchright-python`](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) | 1269 | Python | **强烈推荐**，drop-in 替换 playwright，自动绕检测 |
| [`Kaliiiiiiiiii-Vinyzu/patchright-nodejs`](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-nodejs) | 640 | TS | Node 版 |
| [`Vinyzu/Botright`](https://github.com/Vinyzu/Botright) | 960 | Python | undetected + fingerprint changing + captcha solving 三合一 |
| [`Vinyzu/chrome-fingerprints`](https://github.com/Vinyzu/chrome-fingerprints) | 268 | Python | 1 万个真实 Chrome 指纹采样，配 Botright 用 |
| [`saifyxpro/HeadlessX`](https://github.com/saifyxpro/HeadlessX) | 1847 | TS | 自托管 undetected 浏览器自动化平台，基于 Camoufox |
| [`enetx/surf`](https://github.com/enetx/surf) | 1417 | Go | Go HTTP 客户端，假装 Chrome / Firefox，HTTP/3 + JA3 指纹模拟 |

### 反检测知识库

| Repo | Stars | 说明 |
|---|---|---|
| [`niespodd/browser-fingerprinting`](https://github.com/niespodd/browser-fingerprinting) | 4992 | Bot 检测系统全面分析 + 对策清单，**先看这个再写代码** |

---

## L3 · Content Engine（内容引擎）

### Twitter / X scraping

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`vladkens/twscrape`](https://github.com/vladkens/twscrape) | 2330 | Python | **2025 还在更**，X 账号授权式 scraper，支持搜索 / 用户时间线 / followers / followings |
| [`JustAnotherArchivist/snscrape`](https://github.com/JustAnotherArchivist/snscrape) | 5327 | Python | 老牌社交平台 scraper，覆盖 Twitter / Facebook / Insta / Reddit / Telegram |
| [`Altimis/Scweet`](https://github.com/Altimis/Scweet) | 1303 | Python | 推特无 API key scraper，selenium 驱动 |
| [`mahrtayyab/tweety`](https://github.com/mahrtayyab/tweety) | 651 | Python | tweety-ns，活跃维护 |
| [`nirholas/XActions`](https://github.com/nirholas/XActions) | 189 | HTML | X 自动化全套工具集 + MCP server for AI agents |
| [`1220moritz/reverse-twitter-scraper`](https://github.com/1220moritz/reverse-twitter-scraper) | 29 | Python | 基于 requests 的逆向 scraper |
| [`LXGIC-Studios/xfetch`](https://github.com/LXGIC-Studios/xfetch) | 4 | TS | 仅 cookie 的快速 X CLI scraper |

### Twitter / X 媒体下载

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`AAndyProgram/SCrawler`](https://github.com/AAndyProgram/SCrawler) | 1998 | VB.NET | **多平台通杀**：Twitter / Reddit / Insta / OnlyFans / 等几十站点 |
| [`EltonChou/TwitterMediaHarvest`](https://github.com/EltonChou/TwitterMediaHarvest) | 940 | HTML | 浏览器扩展，一键下推特媒体 |
| [`mmpx12/twitter-media-downloader`](https://github.com/mmpx12/twitter-media-downloader) | 864 | Go | `twmd` CLI/GUI，无需 API |
| [`afkarxyz/Twitter-X-Media-Batch-Downloader`](https://github.com/afkarxyz/Twitter-X-Media-Batch-Downloader) | 377 | TS | GUI 批量下原画质 |
| [`Spark-NF/twitter_media_downloader`](https://github.com/Spark-NF/twitter_media_downloader) | 309 | Python | 老牌 Python 实现 |

### 通用素材下载

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`mikf/gallery-dl`](https://github.com/mikf/gallery-dl) | **17686** | Python | **王者**，300+ 站点支持，包括 Twitter / Reddit / Coomer / Kemono / Pixiv / etc，CLI + cookie 模式 |
| [`mhogomchungu/media-downloader`](https://github.com/mhogomchungu/media-downloader) | 4355 | C++ | Qt GUI 前端，封装 yt-dlp / gallery-dl |
| [`chapmanjacobd/library`](https://github.com/chapmanjacobd/library) | 474 | Python | 99+ CLI 工具，建立和管理本地媒体库 |

### Coomer / Kemono 聚合下载

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`Emy69/CoomerDL`](https://github.com/Emy69/CoomerDL) | 683 | Python | Coomer 下载器 |
| [`AlphaSlayer1964/kemono-dl`](https://github.com/AlphaSlayer1964/kemono-dl) | 595 | Python | 简洁 Kemono 下载 |
| [`Ljzd-PRO/KToolBox`](https://github.com/Ljzd-PRO/KToolBox) | 535 | Python | **高度可定制**的 Kemono.cr / .su / .party 下载 |
| [`Yuvi9587/Kemono-Downloader`](https://github.com/Yuvi9587/Kemono-Downloader) | 434 | Python | PyQt5 GUI 版 |
| [`notFaad/coom-dl`](https://github.com/notFaad/coom-dl) | 425 | Dart | Dart 实现的 Coomer / Kemono 下载 |
| [`VoxDroid/KemonoDownloader`](https://github.com/VoxDroid/KemonoDownloader) | 255 | Python | PyQt6 跨平台 |
| [`e43b/Kemono-and-Coomer-Downloader`](https://github.com/e43b/Kemono-and-Coomer-Downloader) | 242 | Python | Kemono + Coomer 二合一 |
| [`smartacephale/coomer-downloader`](https://github.com/smartacephale/coomer-downloader) | 74 | TS | Coomer / Kemono / Bunkr / GoFile / Reddit-NSFW 通用下载 |

### OnlyFans / Fansly

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`datawhores/OF-Scraper`](https://github.com/datawhores/OF-Scraper) | 1017 | Python | **现役维护最活跃**的 OF 抓取器 |
| [`DIGITALCRIMINAL/ArchivedUltimaScraper`](https://github.com/DIGITALCRIMINAL/ArchivedUltimaScraper) | 954 | Python | OF + Fansly 老牌 |
| [`k0rnh0li0/onlyfans-dl`](https://github.com/k0rnh0li0/onlyfans-dl) | 798 | Python | 经典 OF 下载器 |
| [`Hashirama/OFDL`](https://github.com/Hashirama/OFDL) | 273 | Python | GUI 版 |

### NSFW 内容识别 / 分类

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`notAI-tech/NudeNet`](https://github.com/notAI-tech/NudeNet) | **2314** | Python | **业界标准**，`pip install nudenet`，18 种细粒度标签 + bbox + 置信度 |
| [`vladmandic/nudenet`](https://github.com/vladmandic/nudenet) | 320 | JS | TFJS / NodeJS 版 |
| [`mdietrichstein/tensorflow-open_nsfw`](https://github.com/mdietrichstein/tensorflow-open_nsfw) | 447 | Python | Yahoo Open NSFW 模型 |
| [`MaybeShewill-CV/nsfw-classification-tensorflow`](https://github.com/MaybeShewill-CV/nsfw-classification-tensorflow) | 82 | Python | TensorFlow 实现 |
| [`TheHamkerCat/NSFW_Detection_API`](https://github.com/TheHamkerCat/NSFW_Detection_API) | 69 | Python | 现成 REST API，docker 一键部署 |
| HuggingFace `Falconsai/nsfw_image_detection` | - | - | ViT 模型几 MB，CPU 可跑，准确率 97% |

---

## L4 · Warmup Orchestrator（养号编排）

| Repo | Stars | 语言 | 说明 |
|---|---|---|---|
| [`CryptoBusher/Adspower-twitter-warmup`](https://github.com/CryptoBusher/Adspower-twitter-warmup) | **76** | Python | **金标准**，作者实测 8 个月仅 0.12% 封号率，已写好 5 类拟人化行为：发推 / 必关 / 随机关 / 刷 feed / dodge 弹窗 |
| [`CryptoBusher/Warpcast-adspower-farm`](https://github.com/CryptoBusher/Warpcast-adspower-farm) | 58 | Python | 同作者，Farcaster 版本，逻辑可复用 |
| [`nirholas/XActions`](https://github.com/nirholas/XActions) | 189 | HTML | X 自动化全套工具 + MCP server，可被 Claude / GPT 调用 |
| [`shhalaka/x-bot`](https://github.com/shhalaka/x-bot) | 4 | TS | Multi-account X 自动化 Node.js / TS |
| [`yashu1wwww/Twitter-auto-tweets-with-multiple-accounts`](https://github.com/yashu1wwww/Twitter-auto-tweets-with-multiple-accounts) | 17 | Python | Selenium 多号自动发推 |

---

## 总览统计

- **Browser layer**: 11 repo
- **Content engine**: 25 repo
- **Warmup orchestrator**: 5 repo
- **NSFW classification**: 6 repo
- **总 stars 累计**: 50,000+

足够搭出一条端到端流水线，**不用从 0 写任何一层**。

---

## 选型建议

### 预算 0 元 / 黑客模式
```
patchright-python (browser) 
+ Vinyzu/chrome-fingerprints (假装真实指纹) 
+ twscrape (内容源) 
+ gallery-dl (素材下载) 
+ NudeNet (内容识别) 
+ 自写 warmup loop（参考 CryptoBusher）
```

### 预算 几十刀 / 月 / 推荐
```
AdsPower (10 号免费 / 月，超出付费) 
+ CryptoBusher/Adspower-twitter-warmup (直接用) 
+ twscrape (内容源) 
+ gallery-dl (素材下载) 
+ NudeNet (内容识别)
```

### 商业级 / agency 模式
```
Multilogin / Kameleo (商业指纹浏览器) 
+ 自写编排（基于 CryptoBusher 重构成多线程） 
+ twscrape + 自建 creator DB 
+ NudeNet + 人工二审 
+ 风控告警 + 自动 cool down
```
