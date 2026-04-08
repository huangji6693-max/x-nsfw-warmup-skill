# x-nsfw-warmup-skill

> **Claude Code Skill** —— X (Twitter) 成人内容方向养号自动化全套开源工具集合
>
> 把指纹浏览器编排、内容采集、NSFW 自动识别、拟人化养号循环这四件事，
> 用 20+ 个被验证的开源 repo 拼成一条可跑的流水线。

---

## 它解决什么

成人内容方向的 X 账号运营有两个工程难点：

1. **指纹浏览器没法控制** —— AdsPower / BitBrowser 都有 Local API，但文档分散
2. **没法自动识别成人内容** —— 简单的 sfw/nsfw 二分类不够，需要 18 种细粒度标签

这个 skill 给出了**端到端**的开源解决方案，每一步都有现成 repo，不用从 0 写。

---

## 快速开始

```bash
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill
cd x-nsfw-warmup-skill

# 安装依赖
pip install -r requirements.txt

# 看 skill 主文件
cat SKILL.md

# 看完整工具目录
cat tools-catalog.md

# 跑示例
python examples/02-nudenet-classify.py path/to/image.jpg
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

## 它为什么是 Claude Code Skill

Claude Code 的 skill 系统会在用户说出相关意图时自动加载这个 SKILL.md，然后 Claude 就能：

- 知道用哪个 repo 解决哪个具体痛点
- 直接参照 `examples/` 里跑得通的代码
- 按 `workflows/` 的顺序帮用户搭起完整流水线
- 不需要现场 Google，也不会推荐过时 repo

**安装到本地 Claude Code**：

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill ~/.claude/skills/x-nsfw-warmup
```

之后跟 Claude Code 说"帮我搭一套 X 养号"，它会自动加载这个 skill。

---

## ⚠️ 风险声明

- 自动化行为**违反 X ToS**，封号是常态
- 仅适用于**法律允许成人内容的司法辖区**
- **不要**用于：未成年内容、deepfake、未经同意私照、骚扰
- 商业化请咨询律师

---

## License

MIT
