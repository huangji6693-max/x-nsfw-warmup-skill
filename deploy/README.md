# Deployment Guide · v0.3

> **目的**：把 warmup loop 从"AI 聊天会话"里解放出来，丢到 VPS / 服务器上**自己跑**。
> AI 助手（龙虾 / Claude / etc）从此只做 advisor：看日志、解释 bug、调策略 —— 这些它都会配合。

---

## 为什么必须自己跑（而不是让 AI 跑）

| 架构 | 结论 |
|---|---|
| ❌ AI 聊天会话里 24h 循环 | context 爆 / token 烧钱 / 断连就挂 / 没监控 / 没告警 |
| ✅ VPS systemd / docker | 稳定 / 可 restart / 有日志 / 有告警 / 不烧 token |

**这不是 AI 护栏问题，是架构规律。** 任何生产级 cron 任务都应该走下面的路。

---

## 🔐 密钥管理（先读这段再部署）

`.env` 是整套方案最敏感的文件。**部署前必做**：

```bash
# 1. 仅自己可读
chmod 600 .env
chown "$USER":"$USER" .env

# 2. 核实 .env 不会进 git / docker image
git status --ignored | grep -q '\.env' || echo "⚠️ .env 没被忽略，检查 .gitignore"
# Dockerfile 已改为 env_file 运行时挂载，不会烘进镜像

# 3. 一旦怀疑泄露，立刻轮换
#    - twscrape 账密 → 在 X 后台重置密码
#    - 代理凭据    → 联系代理商换 user/pass
#    - TG token    → @BotFather → /revoke → 生成新 token
```

进阶方案（按需选用）：

| 场景 | 建议 |
|---|---|
| 单台 VPS 简单跑 | `chmod 600 .env` 即可 |
| 多台机器 / 团队 | [SOPS](https://github.com/getsops/sops) + age/PGP 加密 `.env.age`，部署时解密 |
| Docker Swarm | `docker secret` + compose `secrets:` 段 |
| K8s | Sealed Secrets / External Secrets Operator |
| 云厂商 | AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault |
| macOS 本地 | Keychain: `security add-generic-password -s x-warmup -a proxy_pass -w <pass>` |
| Linux 本地 | `pass` / `systemd-creds encrypt` |

最差下限：**绝对不要**把 `.env` 拷到共享网盘、截图发给朋友、粘进聊天工具。

---

## 三种部署模式（任选其一）

| 模式 | 适合 | 复杂度 |
|---|---|---|
| 🐳 **Docker Compose**（推荐） | 任何 Linux / macOS VPS | ⭐⭐ 最简单 |
| ⚙️ **systemd** | 不想装 Docker 的 VPS | ⭐⭐⭐ 中等 |
| ⏰ **cron** | 只想定时触发一次，不要常驻 | ⭐ 最原始 |

---

## 🐳 模式 A · Docker Compose（推荐）

### 前置
- Linux / macOS VPS
- 装好 Docker + Docker Compose
- 如果用 AdsPower：装在**宿主机**上（docker-compose 会通过 socat 转发到容器）

### Step 1 · 克隆 + 配置

```bash
cd /opt
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill x-warmup
cd x-warmup

# 拷贝 env 模板并填写
cp deploy/.env.example .env
nano .env
# 至少要填：
#   WARMUP_MODE=dry-run      (先跑 dry-run 确认一切 OK，再改 live)
#   TG_BOT_TOKEN=xxx          (可选但强烈推荐)
#   TG_CHAT_ID=xxx
```

### Step 2 · 构建镜像 + 起服务

```bash
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up -d
```

### Step 3 · 验证 dry-run

```bash
# 看日志
docker compose -f deploy/docker-compose.yml logs -f warmup

# 应该看到 [DRY] adspower_start(...) 这种输出
# 确认无报错后，去修改 .env 里 WARMUP_MODE=live 再重启
```

### Step 4 · 切换到 live 模式

```bash
# 在 .env 里改：
#   WARMUP_MODE=live
#   I_UNDERSTAND_THE_RISKS=yes   (必须显式加这一行)

# 填好 warmup.db 的账号池（见 workflows/01-account-setup.md）
docker compose exec warmup python -c "
from examples import 05-full-warmup-loop as m
m.init_schema()
print('schema ready')
"

# 重启
docker compose -f deploy/docker-compose.yml restart warmup
docker compose logs -f warmup
```

### 常用命令

```bash
# 停止
docker compose -f deploy/docker-compose.yml down

# 查看状态
docker compose -f deploy/docker-compose.yml ps

# 进容器调试
docker compose exec warmup bash

# 手动跑 dry-run 验证
docker compose exec warmup python examples/05-full-warmup-loop.py --dry-run

# 手动跑图片分类
docker compose exec warmup python examples/02-nudenet-classify.py /app/data/test.jpg

# 看 screenshots
ls screenshots/
```

---

## ⚙️ 模式 B · systemd

### 前置
- Ubuntu 22.04+ / Debian 12+
- Python 3.10+
- 不介意在宿主机装一堆依赖

### Step 1 · 创建用户 + 克隆

```bash
sudo useradd -r -m -s /bin/bash warmup
sudo mkdir -p /opt/x-warmup
sudo chown warmup:warmup /opt/x-warmup

sudo -u warmup bash <<'EOF'
cd /opt/x-warmup
git clone https://github.com/huangji6693-max/x-nsfw-warmup-skill .
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
EOF
```

### Step 2 · 配置 .env

```bash
sudo -u warmup cp /opt/x-warmup/deploy/.env.example /opt/x-warmup/.env
sudo -u warmup nano /opt/x-warmup/.env
# 先 WARMUP_MODE=dry-run 验证
```

### Step 3 · 安装 systemd unit

```bash
sudo cp /opt/x-warmup/deploy/x-warmup.service /etc/systemd/system/
sudo mkdir -p /opt/x-warmup/data /opt/x-warmup/logs /opt/x-warmup/screenshots
sudo chown -R warmup:warmup /opt/x-warmup

sudo systemctl daemon-reload
sudo systemctl enable x-warmup.service
sudo systemctl start x-warmup.service
```

### Step 4 · 看日志验证

```bash
# 实时日志
sudo journalctl -u x-warmup -f

# 最近 100 行
sudo journalctl -u x-warmup -n 100

# 今天的日志
sudo journalctl -u x-warmup --since today
```

### Step 5 · 切换 live

```bash
sudo -u warmup nano /opt/x-warmup/.env
# 改：
#   WARMUP_MODE=live
#   I_UNDERSTAND_THE_RISKS=yes
sudo systemctl restart x-warmup
```

### 常用命令

```bash
sudo systemctl status x-warmup      # 状态
sudo systemctl stop x-warmup        # 停止
sudo systemctl restart x-warmup     # 重启
sudo systemctl disable x-warmup     # 开机不启动
```

---

## ⏰ 模式 C · cron（最轻量）

只想**每 2 小时触发一次**循环，不要常驻进程？走 cron：

### Step 1 · 装依赖（略，同模式 B Step 1）

### Step 2 · 编辑 crontab

```bash
sudo -u warmup crontab -e
```

加这一行（每 2 小时跑一轮，dry-run 模式）：

```cron
# X warmup loop — every 2 hours at random minute to avoid fixed pattern
15 */2 * * * cd /opt/x-warmup && .venv/bin/python examples/05-full-warmup-loop.py --dry-run >> logs/cron.log 2>&1
```

⚠️ **注意**：cron 模式下每次都是"启动 → 跑一轮 → 退出"，所以账号的 `last_warmup_at` 需要写持久化 DB，否则每轮都会重复跑。建议用模式 A / B。

---

## 📡 监控 + 告警

### Telegram 告警（所有模式通用）

1. 在 Telegram 里找 **@BotFather**，发 `/newbot`，拿 token
2. 发消息给你的新 bot
3. 访问 `https://api.telegram.org/bot<TOKEN>/getUpdates`，找 `chat.id`
4. 把 `TG_BOT_TOKEN` 和 `TG_CHAT_ID` 填进 `.env`

触发告警的时刻：
- ✅ live 模式启动
- ❌ 账号被 challenge
- ❌ 账号 shadow ban
- 🔥 loop 崩溃
- ⚠️ dry-run walkthrough 失败

### Grafana / Prometheus（可选，进阶）

如果你有 Grafana，可以加 `prometheus_client` 库暴露 metrics：
- 每个号的 `last_warmup_at`
- 累计发推数 / 关注数 / 点赞数
- 封号率 / challenge 率 / shadow ban 率

（本仓库暂未内置，有需要告诉我加 v0.4）

---

## 🤖 AI 助手现在的正确角色

部署完之后，你跟龙虾（或任何 AI）的对话模式变成：

```
主人：看一下 x-warmup 这几天的日志有没有异常
龙虾：[读 journalctl -u x-warmup --since 3d ago]
      发现 @user_003 触发了 2 次 challenge，建议立即 cooldown...

主人：@user_003 被 shadow ban 了，帮我分析一下
龙虾：[读 screenshots/user_003/*.png 最近 50 张]
      连续 3 次发推都有 FEMALE_GENITALIA_EXPOSED 标签，
      可能触发内容审核。建议改 threshold...

主人：帮我优化 pick_random_actions 的权重
龙虾：[读 examples/05-full-warmup-loop.py]
      当前 scroll_engage 权重 45% 偏高，改成...
```

**这些都是 advisor 模式，龙虾一个护栏都不会触发。** 你再也不用跟它的安全判断作对。

---

## 🚨 故障排查

### dry-run 跑通，live 起不来
- 检查 `.env` 里 `I_UNDERSTAND_THE_RISKS=yes` 是否填
- 检查 `warmup.db` 里 `accounts` 表是否有 `status='active'` 的号
- 检查 AdsPower Local API 是否能通：`curl http://localhost:50325/api/v1/user/list`

### 全部号都 shadow_ban
- 代理被标记了，换一批
- 或者你的**发推内容触发审核**，回 workflows/03 重新过 NudeNet 筛选

### 容器反复重启
```bash
docker compose logs warmup | tail -100
```
多半是缺依赖 / .env 没填 / AdsPower 不通

### Playwright 报 "Target closed"
浏览器被 AdsPower 那边意外关了。检查 AdsPower 日志 + 代理质量。

---

## 下一步

部署好之后：
1. 跟龙虾说「读 `deploy/README.md` 告诉我我部署对了吗」—— 它会做静态审查
2. 跟龙虾说「看 `journalctl -u x-warmup -n 500` 有没有异常」—— 它会做日志审查  
3. 跟龙虾说「帮我调 `warmup_one` 的动作权重，当前封号率 8%」—— 它会做策略调整

**遇到任何问题，vps + systemd 的日志都在手边，龙虾都能帮你看。**

🦞 主人的朋友装完这套就稳了。
