# 🌙 Always-On · 关机问题 & 24/7 运行选项

> **常见疑问**：「我电脑关机了 warmup 还跑吗？」
> **答案**：不跑。但**这其实是好事**，看下面解释。

---

## 反直觉真相：24/7 不停 = bot 信号

很多人第一反应是「我要让它 24 小时不停跑才有效果」。**这是错的**。

真人用 X 是这样的：

```
06:00 ── 起床刷 10 分钟
12:00 ── 午饭刷 5 分钟
18:00 ── 下班路上刷 20 分钟
22:00 ── 睡前刷 30 分钟
23:00 ── 睡觉，8 小时不上线 ──┐
                               │ 真人作息
07:00 ── 起床 ──────────────┘
```

如果你的号 **24 小时不停**，每 2-6 小时来一次精准的 60-180 秒刷推 + 点赞，X 的风控系统会一眼识别出这是 bot。

**CryptoBusher 框架的作者实测 8 个月只封了 0.12% 的号**，他的秘诀里有一条就是「模拟人的作息」—— 让账号有真人的睡眠时间。

**所以：你 Mac 晚上关机，反而让你的号看起来更像真人。**

---

## 不同需求 → 不同方案

| 你的情况 | 推荐方案 |
|---|---|
| MacBook 日常用，正常作息 | 🥉 **方案 A**（默认） |
| MacBook 一直插电源，想夜里也跑 | 🥈 **方案 B**（caffeinate） |
| 想完全自动化，账号 20+ | 🥇 **方案 C**（Mac mini 专机） |
| 50+ 号 + 商业级运营 | 🏆 **方案 D**（VPS + docker） |

---

## 🥉 方案 A · 默认 · 跟着 Mac 走（推荐 5~20 号用户）

**配置：完全不用配。**

你正常用 Mac → 面板在后台 → loop 跑
你关 Mac 睡觉 → 面板停 → 早上开机重新点 ▶ Start

实际效果：

```
你的作息：09:00 开机 ─ 23:00 关机    (14 小时活跃)
账号刷推：每号 2-6 小时一次          ≈ 每号 3-5 次/天
账号睡觉：23:00 ─ 09:00              真人作息
```

**这就是最像人的模式。** 完全够用。

### 唯一注意事项

每天早上重开 Mac 后，记得**打开 AdsPower → 启动 Local API → 打开面板 → 点 ▶ Start**。

可以做成 Mac 登录时自动启动（见方案 C 的 launchd 部分）。

---

## 🥈 方案 B · 不让 Mac 睡眠（适合常插电用户）

如果你的 MacBook 经常插着电源，希望**夜里也跑**：

### 步骤 1 · 用 caffeinate 启动面板

```bash
caffeinate -i -s bash scripts/launch_gui.sh
```

参数：

- `-i` 阻止系统因为 idle 进入睡眠
- `-s` 防止插电状态下的睡眠
- （加 `-d` 可以连显示器都不让黑，但**没必要**，黑屏不影响后台 Python）

**关掉这个终端窗口 = caffeinate 退出 = Mac 恢复正常作息**。

### 步骤 2 · 系统设置兜底

系统偏好设置 → 电池 / 节能 → 连接电源时：

- ☑️ **连接电源适配器时阻止 Mac 自动睡眠**
- ☑️ **唤醒以供网络访问**
- ❌ 不需要勾「显示器关闭后让硬盘进入睡眠」

### ⚠️ MacBook 用户特别提醒

- **插电源时再用方案 B**，否则一夜耗光电池
- 笔记本长期不睡眠对电池寿命有损害（电池循环数会涨）
- 推荐每周给 MacBook 一次完整睡眠（停面板，让它自然休息）

### ⚠️ 别太激进

就算用方案 B，**也建议在 Settings 里设置 `interval_min_hours = 4`** 让每个号每天最多 5-6 次互动，**比一直贴脸刷更安全**。

---

## 🥇 方案 C · Mac mini 专机（账号 20+ 推荐）

二手 M1 Mac mini 大概 ¥3500-4500 RMB / $500-650 USD，性价比最高。

### 配置清单

- Mac mini M1/M2/M3
- 16GB 内存（8GB 也能跑但紧）
- 接显示器或开启屏幕共享 (Screen Sharing)
- 网线接路由器（更稳）
- 装 AdsPower 桌面版
- 装这套 skill

### launchd 自动启动（macOS 原生 cron）

把面板做成开机自启动服务：

**`~/Library/LaunchAgents/com.x-warmup.gui.plist`**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.x-warmup.gui</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup/scripts/launch_gui.sh</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup/logs/launchd.out.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/你的用户名/.openclaw/workspace/skills/x-nsfw-warmup/logs/launchd.err.log</string>
</dict>
</plist>
```

加载并启动：

```bash
launchctl load ~/Library/LaunchAgents/com.x-warmup.gui.plist
launchctl start com.x-warmup.gui
```

之后 Mac mini 每次开机/重启都会自动启动面板。

停止 / 卸载：

```bash
launchctl unload ~/Library/LaunchAgents/com.x-warmup.gui.plist
```

### 远程访问

平时不接显示器：

- macOS 系统设置 → 共享 → 开启 **屏幕共享 (Screen Sharing)**
- 在你的主 Mac 上：访达 → 前往 → 连接服务器 → `vnc://mac-mini.local`
- 浏览器里访问 `http://mac-mini.local:8080` 直接看面板

---

## 🏆 方案 D · VPS + docker 部署（50+ 号 / 商业级）

**前提**：你不再依赖 AdsPower 桌面端的 GUI 操作，完全切换到 patchright（无指纹浏览器）方案，或者用 AdsPower 的 headless 模式 + Linux 服务器版。

**已经有现成的 docker-compose**，看 [`deploy/README.md`](../deploy/README.md)。

适合的场景：

- 100+ 账号需要 7×24 监控
- 团队多人协作
- 需要 Telegram / Grafana 告警
- 已经有 VPS 运维经验

---

## 决策表

```
你养几个号？
    ├── 1-10 个   → 方案 A（关机就关机，正常作息）
    ├── 10-20 个  → 方案 A 或 B（B 适合 MacBook 长期插电）
    ├── 20-50 个  → 方案 C（Mac mini 专机）
    └── 50+ 个    → 方案 D（VPS + docker，需要技术支持）
```

---

## 常见问题

### Q1: 我每天关机重开会丢数据吗？

**不会。** 所有数据存在 `warmup.db` (SQLite)，关机后还在。开机后打开面板就接着用。

### Q2: 为什么不能像普通 cron 一样后台跑？

可以的，但不必要。NiceGUI 面板**关闭浏览器窗口不会停止后台 loop**，只要终端窗口（运行 `python gui/app.py` 的那个）开着就行。

如果想完全无界面：

```bash
nohup bash scripts/launch_gui.sh > logs/gui.log 2>&1 &
```

之后 `tail -f logs/gui.log` 看日志。要停就 `pkill -f "python gui/app.py"`。

### Q3: Mac 睡眠时账号"卡"了会怎样？

**不会卡。** 你 Mac 睡的时候 Python 进程整个被 macOS 暂停，醒来时它从暂停的地方继续。最多就是某个账号的 last_warmup_at 时间戳显示「8 小时前」，下一次循环它会被优先选中。**符合真人「早上一上来先刷一波」的模式**。

### Q4: 我能让某些号 24h 跑，某些号跟作息走吗？

不能直接做，但可以：

- 把"高活跃度号"改大 `interval_max_hours`，让它们在 14h 活跃窗口里高频跑
- 把"低活跃度号"改小 `interval_min_hours`（比如 8h），让它们一天只跑 1-2 次
- 想做更复杂分组的话，需要改代码加 `account_tier` 字段，告诉我我可以加 v0.6

### Q5: 我朋友的电脑关机了，我能远程帮他启动 loop 吗？

**不能远程开机**（除非朋友配了 Wake-on-LAN 或者 Mac 远程桌面）。

但可以：

- 朋友自己开机后，**你通过 Screen Sharing 或 anydesk 进他 Mac**，帮他点 ▶ Start
- 或者朋友设置好方案 C 的 launchd，**开机自动启动**，他完全不用动
- 或者方案 D，永远不停

---

## TL;DR

| | |
|---|---|
| **最常见情况** | 你的 Mac 关机时 loop 停。**这是好事，不是坏事**，符合真人作息 |
| **5-20 个号** | 方案 A 默认就够 |
| **想夜里也跑** | 方案 B `caffeinate -i -s bash scripts/launch_gui.sh` |
| **想 7×24 全自动** | 方案 C Mac mini 专机 + launchd 自启动 |
| **企业级 100+** | 方案 D VPS docker（已有 deploy/ 套件） |

🦞 **不要为了"24/7"而 24/7**，X 风控会感谢你的 Mac 关机。
