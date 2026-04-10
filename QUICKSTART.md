# 🦞 QUICKSTART · 一页纸傻瓜教程

> **读者：** 完全没技术基础，但有 X 账号 + AdsPower 的朋友
> **目标：** 15 分钟内把你的号接入 warmup 系统
> **系统：** Mac（Windows 看文末附录）
> **中文别名：** 新手必读

---

## 🎁 最新：可视化控制面板（最省事）

如果你**完全不想碰命令行**，跳过下面所有步骤，直接用网页面板：

```bash
# 第 1 步 装
curl -fsSL https://raw.githubusercontent.com/huangji6693-max/x-nsfw-warmup-skill/main/scripts/install.sh | bash

# 第 2 步 启动面板（按提示进入安装目录后跑这一条）
bash scripts/launch_gui.sh
```

之后浏览器自动打开 `http://localhost:8080`，你看到的是这样的网页：

```
┌─────────────────────────────────────────────┐
│  🦞 X Warmup Skill · Control Panel          │
├─────────────────────────────────────────────┤
│  [Dashboard]  [Accounts]  [Settings]        │
│  [AdsPower]                                  │
├─────────────────────────────────────────────┤
│                                              │
│   Total: 5    Active: 5    Cooldown: 0      │
│                                              │
│   Status: STOPPED      Mode: dry-run ✅      │
│                                              │
│   [▶ Start]  [■ Stop]                        │
│                                              │
│   Live log:                                  │
│   ┌─────────────────────────────────────┐   │
│   │ 2026-04-10 14:30  warmup_start ...  │   │
│   │ 2026-04-10 14:31  scroll_engage ... │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**所有操作都是点鼠标**：
- **AdsPower 标签** → 点"Test connection" → 自动列出你的 profile → 给每个填 X 用户名 → 点"Add to pool"
- **Settings 标签** → 拖滑条改频率
- **Dashboard 标签** → 点 ▶ Start 启动

🎯 **你不需要敲一行命令、不需要写 SQL、不需要看任何文档。**

⚠️ 第一次跑务必保持 **dry-run 开关 = 开**（默认就是开），看几个小时确认没问题再切 live。

> 详细 GUI 文档：[gui/README.md](./gui/README.md)

---

## 👇 下面是命令行教程（如果你不用网页面板才看这里）

---

## 😌 你不用怕，整个过程就 4 步

**最简单的用法：把这份教程整个发给龙虾，告诉它「照着帮我执行」，让它全程带你。**

如果你想自己做，继续往下看。

---

## 🎯 开始之前，准备 3 样东西

### ① AdsPower 必须已经开着 ✅

桌面端图标要亮着，在 Dock 里能看到。

### ② AdsPower 的 Local API 必须打开 ✅

打开 AdsPower → 左下角「设置」→ 左侧菜单「本地 API」→ 开关打到**开启**状态。

你应该能看到一行地址：`http://local.adspower.net:50325`

**如果你找不到这个选项**：AdsPower 版本太老，先去官网升级一下。

### ③ 你的 X 账号必须已经在 AdsPower profile 里手动登录过 ✅

- 在 AdsPower 里选一个 profile → 点「打开」→ 浏览器弹出 → 访问 `x.com` → 输账号密码登录
- **确保这次登录成功了**（能看到 X 首页，不是登录页）
- 每个号都要这样做一遍（首次登录没法自动化）

**如果 X 要你验证手机号/邮箱**：必须通过，否则这个号没法用。

---

## 🚀 然后就只剩 4 步

### 第 1 步 · 打开「终端」

按住 `⌘ Command` + 按空格键 → 弹出搜索框 → 输入 `终端` → 按回车

> 会弹出一个黑底白字的小窗口，别慌，这就是终端。你只需要**复制粘贴**，不用打字。

---

### 第 2 步 · 复制下面这一整行，粘贴进终端，按回车

```bash
curl -fsSL https://raw.githubusercontent.com/huangji6693-max/x-nsfw-warmup-skill/main/scripts/install.sh | bash
```

**然后等 3~5 分钟**。终端会刷一堆英文和进度条，别担心，这是在自动安装。

✅ **成功的样子**：最后看到类似这样的几行：

```
================================
✅ Install complete.
================================

Skill location:
  /Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup

Next step — onboard your existing accounts:

  cd /Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup
  source .venv/bin/activate
  python scripts/onboard.py
```

❌ **如果你看到红色 `[x]` 开头的错误**：把整段输出截图发给帮你的人（或龙虾），问"这个错误怎么办"。

---

### 第 3 步 · 复制终端告诉你的那 3 条命令，一次一条粘贴

上面第 2 步结尾，终端会打印出 3 条命令（就是上面蓝色加粗的那 3 行）。

**把它们一条一条复制粘贴进终端**，每条回车执行一次。

典型来说这 3 条长这样：

```bash
cd /Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup
source .venv/bin/activate
python scripts/onboard.py
```

> 别手打，容易错。一定用**复制粘贴**。

---

### 第 4 步 · 跟着向导回答 5 个问题

终端会弹出一个菜单，长这样：

```
🦞  X Warmup Skill · Onboarding Wizard
==========================================

[1/5] Which fingerprint browser do you use?
  [1] AdsPower
  [2] BitBrowser
  [3] Other / manual
  >
```

**在 `>` 后面输入数字、回车**。5 个问题一步步往下走：

---

#### 问题 1：你用什么指纹浏览器？

```
[1/5] Which fingerprint browser do you use?
  > 1                    ← 你输入 1 回车（AdsPower）
```

---

#### 问题 2：AdsPower API 地址？

```
[AdsPower Local API URL]
  [http://local.adspower.net:50325]
  >                      ← 什么都不输，直接回车（用默认）
```

---

#### 问题 3：导入哪些 profile？

向导会**自动抓出你 AdsPower 里所有的 profile**，长这样：

```
[3/5] Pick which profiles to import
  [ 1] vn_alice_001       id=ads_abc123
  [ 2] vn_bella_002       id=ads_def456
  [ 3] vn_carol_003       id=ads_ghi789
  [a] all (3)
  > a                     ← 输入 a 回车（全导）
```

> 如果你只想导一部分，输 `m` 然后输入序号，比如 `1,3` 就是导第 1 和第 3 个。

---

#### 问题 4：每个号的 X 用户名是什么？

向导会**一个一个问你**：

```
[4/5] Enter X handle for each profile

  vn_alice_001 → @        ← 你打 alice_cute_xx 回车（不要带 @ 符号）
  vn_bella_002 → @        ← 你打 bella_nsfw 回车
  vn_carol_003 → @        ← 直接回车=跳过这个不导
```

> **这里最关键** —— 你要知道 AdsPower 里哪个 profile 对应 X 上的哪个用户名。
>
> 如果忘了，可以：
> - 去 AdsPower 里打开那个 profile，看浏览器里 X 登录的是谁
> - 或者在 AdsPower 的 profile 备注里找

---

#### 问题 5（自动完成）：写入数据库

向导会自动跑完，最后告诉你：

```
[5/5] Write to warmup.db
  [+] inserted 3 new, updated 0 existing
  [+] total active accounts in DB: 3

==========================================
✅ Onboarding complete
==========================================

  3 account(s) ready in warmup.db
```

**看到 `✅ Onboarding complete` 就成功了！** 🎉

---

## 🎯 成功后你有什么

- 你的 X 账号已经进 warmup.db 数据库
- 每个号绑好了 AdsPower profile
- 系统随时可以接管这些号
- **但现在还只是 dry-run 演示状态**，不会真的发推

---

## 🚦 下一步（可选，看你要不要真的跑 live）

### 只想先看看流程是怎么跑的（不动真账号）

在终端里继续运行：

```bash
python examples/05-full-warmup-loop.py --dry-run
```

屏幕上会刷一堆 `[DRY] page.goto(...)` 之类的假日志，告诉你这个循环会做什么。**完全不会动你的号**。

---

### 真的要跑 live（真实发推 / 关注 / 刷 feed）

**⚠️ 这一步会真的操作你的 X 账号，可能导致封号。** 只在你想清楚了的时候做。

切 live 要改配置 + 手动确认一次，细节见 `deploy/README.md`。

**建议先让你的技术朋友或者龙虾帮你 review 一遍**，不要自己瞎切。

---

## 🆘 常见问题

### Q1: 终端粘贴的时候没反应

Mac 的终端粘贴快捷键是 `⌘ Command` + `V`。右键也行。

---

### Q2: 看到很多红色 `error` 或 `[x]`

**不要紧张。** 截图整个终端窗口，发给：
- 你的技术朋友
- 或者直接发给龙虾，说"帮我看这个错误"

90% 的错都是：
- AdsPower 没开
- AdsPower Local API 没打开
- 网络不好，下载失败（等 1 分钟重试）

---

### Q3: 向导说 "can't reach http://local.adspower.net:50325"

回去确认**第 ②步** —— AdsPower 的 Local API 没打开。

---

### Q4: 我填错了 handle 怎么办

打开终端，运行：

```bash
python scripts/add_account.py --handle 新用户名 --profile-id ads_abc123 --browser adspower
```

它会自动覆盖之前的错误记录。

---

### Q5: 我想重新来一次

删数据库然后重跑向导：

```bash
rm warmup.db
python scripts/onboard.py
```

---

### Q6: 我想看现在数据库里有几个号

```bash
python scripts/check_prereqs.py
```

它会输出一份报告，里面有一行：
```
✅ accounts: 3 rows (3 active)
```

---

## 🦞 最简单的打开方式：让龙虾带你做

如果你觉得上面还是太复杂，**把这整份教程原文发给龙虾**，然后说：

> "按这份教程，一步一步带我执行。每一步执行完告诉我屏幕上应该看到什么，等我确认了再进下一步。"

龙虾会：
1. 帮你跑命令
2. 每一步验证结果
3. 错了帮你排查
4. 把 5 个向导问题一个一个翻译给你看

**这是最省心的方式**，你全程只需要：
- 手动打开 AdsPower 确认一下
- 复制粘贴命令
- 看到结果告诉龙虾"我看到 XXX 了"
- 向导问号的时候告诉龙虾 X handle 是啥

---

## 📌 Windows 用户附录

Windows 用户暂不完全支持，建议：
- 用 **WSL2**（Windows 内置的 Linux 子系统），然后照着 Mac 教程操作
- 或者换台 Mac / Linux 服务器

AdsPower Windows 版的 Local API 端口一样是 `50325`，wizard 会认。

---

## 🎬 完事之后

你现在：

- ✅ 装好了 skill
- ✅ 号已经进 warmup.db
- ✅ 能跑 dry-run 看流程

**接下来的事（扩展 / 改策略 / 切 live）都交给龙虾或者你的技术朋友，你不用再敲命令了。**

🍷 祝好运。
