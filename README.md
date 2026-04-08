# x-nsfw-warmup-skill 🦞

> **Universal AI-assistant skill** —— X (Twitter) 成人内容方向养号自动化全套开源工具集合
>
> ✅ Works with **OpenClaw** (drop into `~/.openclaw/skills/`)
> ✅ Works with **Claude Code** (drop into `~/.claude/skills/`)
> ✅ Works with **Cursor / Windsurf / LobeChat / any markdown-aware AI tool**
>
> 把指纹浏览器编排、内容采集、NSFW 自动识别、拟人化养号循环这四件事，
> 用 30+ 个被验证的开源 repo 拼成一条可跑的流水线。

---

## 它解决什么

成人内容方向的 X 账号运营有两个工程难点：

1. **指纹浏览器没法控制** —— AdsPower / BitBrowser 都有 Local API，但文档分散
2. **没法自动识别成人内容** —— 简单的 sfw/nsfw 二分类不够，需要 18 种细粒度标签

这个 skill 给出了**端到端**的开源解决方案，每一步都有现成 repo，不用从 0 写。

---

## 安装方式（任选一种）

### 🦞 OpenClaw 用户

```bash
# 方式 A · 直接 clone 到 OpenClaw skills 目录
mkdir -p ~/.openclaw/skills
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill ~/.openclaw/skills/x-nsfw-warmup

# 方式 B · 在 OpenClaw 对话里直接粘 GitHub 链接（最快）
# 在任何 OpenClaw 接入的聊天渠道（WhatsApp / Telegram / Slack / 微信 / 飞书…）发：
# "use https://github.com/huangji6693-max/x-nsfw-warmup-skill"
# 它会自动 clone + 注册 + 装依赖

# 方式 C · 通过 ClawHub 安装（如果已发布到 registry）
clawhub install huangji6693-max/x-nsfw-warmup
```

安装后重启 OpenClaw gateway，问它 "帮我搭一套 X 养号" 就会自动唤起这个 skill。

### 🤖 Claude Code 用户

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill ~/.claude/skills/x-nsfw-warmup
```

下次 Claude Code 启动时自动加载。

### 🛠 其他工具（Cursor / Windsurf / LobeChat / 网页 ChatGPT / Claude.ai）

```bash
# 直接 clone 看 markdown
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill
cd x-nsfw-warmup-skill

# 把 SKILL.md + 任何一个 workflow 文件复制粘贴到对话框作上下文
cat SKILL.md workflows/04-warmup-loop.md
```

### 直接跑代码（不依赖任何 AI 客户端）

```bash
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill
cd x-nsfw-warmup-skill

pip install -r requirements.txt
playwright install chromium

python examples/02-nudenet-classify.py path/to/image.jpg
bash examples/04-gallery-dl-batch.sh
```

---

## 文件结构

```
x-nsfw-warmup-skill/
├── SKILL.md                  # 主 skill 文件（Claude Code 调用入口）
├── README.md                 # 你正在看
├── tools-catalog.md          # 完整工具目录（30+ repo + stars + 用途）
├── workflows/
│   ├── 01-account-setup.md       # 账号池 + 指纹 + 代理准备
│   ├── 02-content-sourcing.md    # twscrape 找成人内容源
│   ├── 03-nsfw-classification.md # NudeNet 自动分类
│   └── 04-warmup-loop.md         # 养号循环编排
├── examples/
│   ├── 01-twscrape-search.py     # 关键词搜索 + 用户时间线
│   ├── 02-nudenet-classify.py    # NudeNet 图片分类
│   ├── 03-adspower-control.py    # AdsPower API 启停 profile
│   ├── 04-gallery-dl-batch.sh    # gallery-dl 批量下载
│   └── 05-full-warmup-loop.py    # 串起来的完整 demo
├── requirements.txt
└── LICENSE
```

---

## 核心 repo 速查

### 指纹浏览器（L2）
| repo | stars | 一句话 |
|---|---|---|
| [CryptoBusher/Adspower-twitter-warmup](https://github.com/CryptoBusher/Adspower-twitter-warmup) | 76 | **完整养号框架**，作者实测 8 个月 0.12% 封号率 |
| [AdsPower/localAPI](https://github.com/AdsPower/localAPI) | 107 | AdsPower 官方 Local API |
| [itbrowser-net/undetectable-fingerprint-browser](https://github.com/itbrowser-net/undetectable-fingerprint-browser) | 504 | 免费开源 Multilogin 替代品 |
| [Kaliiiiiiiiii-Vinyzu/patchright-python](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) | 1269 | undetected Playwright |
| [Vinyzu/Botright](https://github.com/Vinyzu/Botright) | 960 | undetected + 改指纹 + 解 captcha 三合一 |
| [botswin/BotBrowser](https://github.com/botswin/BotBrowser) | 2319 | 自带绕 Cloudflare / Akamai |

### 内容源（L3）
| repo | stars | 一句话 |
|---|---|---|
| [vladkens/twscrape](https://github.com/vladkens/twscrape) | 2330 | **2025 还在更**的 X scraper，带授权 |
| [JustAnotherArchivist/snscrape](https://github.com/JustAnotherArchivist/snscrape) | 5327 | 老牌社交平台 scraper |
| [Altimis/Scweet](https://github.com/Altimis/Scweet) | 1303 | 推特无 API key scraper |
| [mahrtayyab/tweety](https://github.com/mahrtayyab/tweety) | 651 | 推特 scraper Python |
| [mikf/gallery-dl](https://github.com/mikf/gallery-dl) | 17686 | **300+ 站点通用下载器** |
| [AAndyProgram/SCrawler](https://github.com/AAndyProgram/SCrawler) | 1998 | Twitter / Reddit / OF / Insta 通杀 |
| [datawhores/OF-Scraper](https://github.com/datawhores/OF-Scraper) | 1017 | OnlyFans 现役维护最活跃 |
| [Ljzd-PRO/KToolBox](https://github.com/Ljzd-PRO/KToolBox) | 535 | Kemono 高定制下载 |
| [mmpx12/twitter-media-downloader](https://github.com/mmpx12/twitter-media-downloader) | 864 | `twmd` Go CLI |

### NSFW 识别（L3）
| repo | stars | 一句话 |
|---|---|---|
| [notAI-tech/NudeNet](https://github.com/notAI-tech/NudeNet) | 2314 | **业界标准**，18 种细粒度标签 |
| [vladmandic/nudenet](https://github.com/vladmandic/nudenet) | 320 | TFJS / NodeJS 版 |
| HuggingFace `Falconsai/nsfw_image_detection` | - | ViT 模型几 MB，CPU 可跑 |

### 养号编排（L4）
| repo | stars | 一句话 |
|---|---|---|
| [CryptoBusher/Adspower-twitter-warmup](https://github.com/CryptoBusher/Adspower-twitter-warmup) | 76 | 主框架，已写好 5 类拟人化行为 |
| [nirholas/XActions](https://github.com/nirholas/XActions) | 189 | X 自动化全套工具 + MCP server |

---

## 它为什么是一个"通用 AI skill"

`SKILL.md` 顶部的 frontmatter 同时声明了 **OpenClaw** 和 **Claude Code** 两套元数据：

```yaml
---
name: x-nsfw-warmup
description: Use when user wants to build, debug, or scale an X (Twitter) account farm focused on adult / NSFW content...
metadata:
  openclaw:
    emoji: 🦞
    requires:
      bins: [python3, pip]
    install:
      - id: pip-deps
        kind: pip
        module: -r requirements.txt
      - id: playwright-chromium
        kind: shell
        command: playwright install chromium
  claude-code:
    type: knowledge-skill
    auto-load-on:
      - "推特养号"
      - "twitter warmup"
      - "AdsPower"
---
```

任意一个 AI 客户端加载后就能：

- 知道用哪个 repo 解决哪个具体痛点
- 直接参照 `examples/` 里跑得通的代码
- 按 `workflows/` 的顺序帮用户搭起完整流水线
- 自动 `pip install -r requirements.txt`（OpenClaw 会读 install 块自动跑）
- 不需要现场 Google，也不会推荐过时 repo

---

## ⚠️ 风险声明

- 自动化行为**违反 X ToS**，封号是常态
- 仅适用于**法律允许成人内容的司法辖区**
- **不要**用于：未成年内容、deepfake、未经同意私照、骚扰
- 商业化请咨询律师

---

## License

MIT
