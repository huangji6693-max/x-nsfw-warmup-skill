# 🦞 GUI Mode · Visual Control Panel

> A local, zero-terminal control panel for the X warmup skill. 
> Designed for users who want to **change frequency and account pool from a visual dashboard** instead of editing YAML or SQL.

---

## What this is

A NiceGUI web panel running locally on `http://localhost:8080`:

- **Dashboard** · account counters, start/stop scheduler, live log stream
- **Accounts** · add / update / delete X accounts + fingerprint profile IDs
- **Settings** · sliders for frequency, session duration, like probability, dry-run toggle
- **AdsPower** · test connection + bulk import profiles from your running AdsPower

**Simplified action set** (vs the full v0.4 warmup loop): scroll feed + occasional like + idle. **No posting, no following, no content sourcing.** This is the "low-commitment" warmup mode.

---

## Install

From the repo root:

```bash
# 1. install the skill (if you haven't yet)
bash scripts/install.sh

# 2. activate venv
source .venv/bin/activate   # or your install dir's .venv

# 3. install GUI deps
pip install -r gui/requirements.txt
```

---

## Run

```bash
python gui/app.py
```

Or the one-liner launcher (handles venv + install check):

```bash
bash scripts/launch_gui.sh
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

The first time you open it, the DB is auto-created and default settings are seeded. Nothing real happens until you:

1. Go to **Accounts** or **AdsPower** tab → add at least one account
2. Go to **Settings** → double-check dry-run is ON (default)
3. Go back to **Dashboard** → click **▶ Start**

You'll see `[DRY]` events streaming in the live log. That means the scheduler is running in safe mode.

---

## Switching to live mode

Once you've verified dry-run runs for 30+ minutes without errors:

1. Go to **Settings** tab
2. Turn OFF the **Dry-run mode** switch
3. Click **■ Stop** then **▶ Start** on the Dashboard to restart the scheduler with the new setting

⚠️ **In live mode**, the scheduler will:
- Actually start AdsPower profiles
- Actually open X in those profiles
- Actually scroll the feed
- Actually click the like button (~10% of scroll ticks, configurable)

It will **not**:
- Post tweets
- Follow anyone
- Unfollow anyone
- Access DMs
- Do anything outside scroll+like

This is by design — the GUI mode is the minimal-risk mode.

---

## Settings reference

| Setting | Default | What it does |
|---|---|---|
| `dry_run` | `true` | No real API calls. Stay on until you've tested |
| `interval_min_hours` | `2.0` | Minimum hours between warmups per account |
| `interval_max_hours` | `6.0` | Maximum hours between warmups per account (currently unused but reserved) |
| `session_min_seconds` | `60` | Minimum duration per warmup session |
| `session_max_seconds` | `180` | Maximum duration per warmup session |
| `like_probability` | `0.10` | Chance to like a visible tweet on each scroll tick |
| `max_concurrent` | `1` | How many accounts can warm up at the same time (keep at 1 for safety) |
| `adspower_api` | `http://local.adspower.net:50325` | AdsPower Local API URL |

All settings are hot-reloadable — change them in the UI and the next loop tick picks them up. No restart needed.

---

## Troubleshooting

### "Cannot reach AdsPower API"
- Is AdsPower desktop running?
- Settings → API → Local API enabled?
- Is the URL correct? (test with `curl http://local.adspower.net:50325/api/v1/user/list`)

### "nicegui not installed"
```bash
pip install -r gui/requirements.txt
```

### Scheduler won't start
- Check you have at least one account in the **Accounts** tab
- Check account status is `active` (not `cooldown` / `banned` / etc)
- Check dry-run is ON for first runs

### Account stuck in cooldown
- Cooldown means the last warmup triggered a `challenge` detection
- Go to AdsPower manually, open that profile, pass the challenge
- In the Accounts tab, edit the account to set status back to `active`

### Web panel won't open
- Is port 8080 in use? Change with `ui.run(port=8081)` in `gui/app.py`
- Check firewall on macOS (it may block localhost 8080 on first run)

---

## Architecture

```
gui/
├── db.py         shared SQLite helpers (accounts / settings / events)
├── adspower.py   AdsPower Local API wrapper with dry-run fake Page
├── engine.py     background scheduler + 2 simplified actions
└── app.py        NiceGUI panel (4 tabs)

                    ┌──────────────┐
                    │  Browser     │  http://localhost:8080
                    │  (you)       │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  NiceGUI     │  gui/app.py
                    │  panel       │
                    └──┬──────┬────┘
                       │      │
       ┌───────────────┘      └──────────────┐
       ▼                                      ▼
┌──────────────┐                       ┌──────────────┐
│  warmup.db   │◄──────────────────────│  Scheduler   │
│  (SQLite)    │   reads settings       │  (asyncio)   │
│              │   writes events        │              │
└──────────────┘                       └──────┬───────┘
                                              │
                                       ┌──────▼──────┐
                                       │  AdsPower   │
                                       │  Local API  │
                                       └─────────────┘
```

The scheduler runs as a background asyncio task in the same process as the UI. When you click **▶ Start**, it enters a loop that:

1. Reads current settings from DB
2. Picks the next eligible account (oldest `last_warmup_at`, past cooldown)
3. Opens AdsPower profile (or fake page in dry-run)
4. Runs `scroll_engage` (90% weight) or `idle` (10% weight)
5. Updates `last_warmup_at` and logs events
6. Sleeps 30-120s before the next account
7. Repeat until you click **■ Stop**

---

## ⚠️ "我电脑关机了 loop 还跑吗？"

**不跑。** 但这是好事 —— 真人也睡觉，账号 24/7 不停反而是 bot 信号。

完整解释 + 4 种 24/7 选项（caffeinate / Mac mini 专机 / VPS / launchd 自启动）见：

👉 [**ALWAYS-ON.md**](./ALWAYS-ON.md)

简短版：

| 你的情况 | 推荐做法 |
|---|---|
| 5-20 号，正常用 Mac | 默认就行，关机就关机 |
| 想夜里也跑（MacBook 插电源） | `bash scripts/launch_gui_keepawake.sh` |
| 想完全 24/7 自动 | 见 [ALWAYS-ON.md §方案 C/D](./ALWAYS-ON.md) |

---

## Going beyond GUI mode

If you want the full feature set (post tweets, follow creators, content sourcing with NudeNet), use the CLI path instead:

- `examples/05-full-warmup-loop.py` (with `deploy/` kit for production)
- `scripts/onboard.py` / `scripts/add_account.py` to manage accounts
- See the root `README.md` and `SKILL.md`

Both paths share the same `warmup.db` so you can use the GUI for day-to-day and occasionally drop into CLI for batch operations.
