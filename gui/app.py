"""
gui/app.py · NiceGUI main panel

Run with:
    cd gui && python app.py
    # or: bash scripts/launch_gui.sh

Opens in browser at http://localhost:8080

Tabs:
  - Dashboard  overview stats, start/stop toggle, live log stream
  - Accounts   add / remove / enable / disable X accounts
  - Settings   frequency (interval, session duration, like prob), dry-run switch
  - AdsPower   connection test + profile import helper
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Allow running as a script from gui/ directory
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from gui import db, engine
    from gui.adspower import AdsPowerClient
else:
    from . import db, engine
    from .adspower import AdsPowerClient

try:
    from nicegui import ui, app as nicegui_app
except ImportError:
    print("❌ nicegui not installed. Run: pip install nicegui")
    print("   Or: pip install -r gui/requirements.txt")
    sys.exit(1)


# ============================================================================
# Bootstrap DB on module load
# ============================================================================
db.bootstrap()


# ============================================================================
# Shared state for reactive updates
# ============================================================================
state = {
    "last_event_id": 0,
    "log_lines": [],
}


def fmt_ts(ts) -> str:
    if not ts:
        return ""
    try:
        return str(ts).split(".")[0]
    except Exception:
        return str(ts)


def status_color(status: str) -> str:
    return {
        "active": "positive",
        "cooldown": "warning",
        "shadow_ban": "negative",
        "challenge": "warning",
        "logged_out": "negative",
        "banned": "negative",
    }.get(status, "grey")


# ============================================================================
# Dashboard tab
# ============================================================================
def render_dashboard():
    with ui.column().classes("w-full gap-4"):
        ui.label("🦞 X Warmup · Dashboard").classes("text-2xl font-bold")

        # ---- counters ----
        counters = {}
        with ui.row().classes("w-full gap-4"):
            for label, key, color in [
                ("Total", "total", "primary"),
                ("Active", "active", "positive"),
                ("Cooldown", "cooldown", "warning"),
                ("Shadow Ban", "shadow_ban", "negative"),
                ("Challenge", "challenge", "warning"),
                ("Logged Out", "logged_out", "negative"),
            ]:
                with ui.card().classes("w-40"):
                    ui.label(label).classes("text-sm text-grey")
                    counters[key] = ui.label("0").classes(f"text-3xl text-{color} font-bold")

        # ---- mode + run toggle ----
        with ui.row().classes("w-full items-center gap-4 mt-2"):
            run_label = ui.label("Status: STOPPED").classes("text-lg")
            mode_label = ui.label("Mode: dry-run").classes("text-lg")
            start_btn = ui.button("▶ Start", color="positive")
            stop_btn = ui.button("■ Stop", color="negative")

        async def do_start():
            db.log_event("user_action", "Start clicked")
            await engine.scheduler.start()
            ui.notify("Scheduler started", color="positive")

        async def do_stop():
            db.log_event("user_action", "Stop clicked")
            await engine.scheduler.stop()
            ui.notify("Scheduler stopped", color="warning")

        start_btn.on_click(do_start)
        stop_btn.on_click(do_stop)

        # ---- live log ----
        ui.label("Live log").classes("text-lg font-bold mt-4")
        log_widget = ui.log(max_lines=200).classes("w-full h-64 bg-black text-green-400 font-mono text-xs")

        # ---- refresh timer ----
        def refresh():
            counts = db.account_counts()
            for k, widget in counters.items():
                widget.set_text(str(counts.get(k, 0)))

            settings = engine.load_settings()
            running = engine.scheduler.is_running()
            run_label.set_text(f"Status: {'RUNNING' if running else 'STOPPED'}")
            mode_label.set_text(f"Mode: {'dry-run ✅' if settings.dry_run else 'LIVE ⚠️'}")

            # Stream new events into the log
            new_events = db.events_since(state["last_event_id"], limit=100)
            if new_events:
                for ev in new_events:
                    line = f"{fmt_ts(ev['ts'])}  [{ev['event_type']}]  {ev['detail'] or ''}"
                    log_widget.push(line)
                state["last_event_id"] = new_events[-1]["id"]

        ui.timer(2.0, refresh)
        refresh()  # initial


# ============================================================================
# Accounts tab
# ============================================================================
def render_accounts():
    with ui.column().classes("w-full gap-4"):
        ui.label("👥 Accounts").classes("text-2xl font-bold")

        accounts_table = ui.table(
            columns=[
                {"name": "handle", "label": "Handle", "field": "handle", "align": "left"},
                {"name": "profile", "label": "Profile ID", "field": "fingerprint_profile_id", "align": "left"},
                {"name": "browser", "label": "Browser", "field": "fingerprint_browser", "align": "left"},
                {"name": "status", "label": "Status", "field": "status", "align": "left"},
                {"name": "last", "label": "Last warmup", "field": "last_warmup_at", "align": "left"},
                {"name": "notes", "label": "Notes", "field": "notes", "align": "left"},
            ],
            rows=[],
            row_key="handle",
        ).classes("w-full")

        # ---- add account row ----
        ui.label("Add account").classes("text-lg font-bold mt-4")
        with ui.row().classes("w-full gap-2 items-end"):
            new_handle = ui.input(label="Handle", placeholder="alice_cute").classes("flex-1")
            new_profile = ui.input(label="AdsPower Profile ID", placeholder="ads_abc123").classes("flex-1")
            new_browser = ui.select(["adspower", "bitbrowser", "manual", "patchright"], value="adspower", label="Browser")
            new_notes = ui.input(label="Notes (optional)").classes("flex-1")

            def add_clicked():
                h = new_handle.value.strip().lstrip("@")
                p = new_profile.value.strip()
                if not h or not p:
                    ui.notify("handle and profile id are required", color="warning")
                    return
                inserted = db.upsert_account(h, p, new_browser.value, notes=new_notes.value or "")
                ui.notify(f"{'inserted' if inserted else 'updated'} @{h}", color="positive")
                new_handle.set_value("")
                new_profile.set_value("")
                new_notes.set_value("")
                refresh_table()

            ui.button("Add / Update", color="primary").on_click(add_clicked)

        # ---- danger zone ----
        ui.label("Remove account").classes("text-lg font-bold mt-4 text-red-500")
        with ui.row().classes("w-full gap-2 items-end"):
            del_handle = ui.input(label="Handle to delete", placeholder="alice_cute").classes("flex-1")

            def delete_clicked():
                h = del_handle.value.strip().lstrip("@")
                if not h:
                    return
                db.delete_account(h)
                ui.notify(f"deleted @{h}", color="warning")
                del_handle.set_value("")
                refresh_table()

            ui.button("Delete", color="negative").on_click(delete_clicked)

        def refresh_table():
            accounts_table.rows = db.list_accounts()
            accounts_table.update()

        refresh_table()
        ui.timer(5.0, refresh_table)


# ============================================================================
# Settings tab
# ============================================================================
def render_settings():
    with ui.column().classes("w-full gap-4 max-w-2xl"):
        ui.label("⚙️ Settings").classes("text-2xl font-bold")
        ui.label("Changes apply to the next scheduler tick. No restart needed.").classes("text-sm text-grey")

        settings = db.load_all_settings()

        # ---- dry run ----
        with ui.card().classes("w-full"):
            ui.label("Safety").classes("text-lg font-bold")
            dry_run_switch = ui.switch(
                "Dry-run mode (no real AdsPower / X calls)",
                value=settings.get("dry_run", "true").lower() == "true",
            )

            def on_dry_run_change(e):
                db.set_setting("dry_run", "true" if e.value else "false")
                ui.notify(f"dry-run: {'ON' if e.value else 'OFF'}",
                          color="positive" if e.value else "warning")
            dry_run_switch.on_value_change(on_dry_run_change)

        # ---- frequency ----
        with ui.card().classes("w-full"):
            ui.label("Frequency").classes("text-lg font-bold")

            ui.label("Min hours between warmups per account")
            interval_min = ui.slider(
                min=0.5, max=24.0, step=0.5,
                value=float(settings.get("interval_min_hours", "2.0")),
            ).props("label-always")

            ui.label("Max hours between warmups per account")
            interval_max = ui.slider(
                min=1.0, max=48.0, step=0.5,
                value=float(settings.get("interval_max_hours", "6.0")),
            ).props("label-always")

            def on_interval_min(e):
                db.set_setting("interval_min_hours", str(e.value))
            def on_interval_max(e):
                db.set_setting("interval_max_hours", str(e.value))
            interval_min.on_value_change(on_interval_min)
            interval_max.on_value_change(on_interval_max)

        # ---- session duration ----
        with ui.card().classes("w-full"):
            ui.label("Session duration").classes("text-lg font-bold")

            ui.label("Min seconds per warmup session")
            session_min = ui.slider(
                min=30, max=600, step=10,
                value=int(float(settings.get("session_min_seconds", "60"))),
            ).props("label-always")

            ui.label("Max seconds per warmup session")
            session_max = ui.slider(
                min=60, max=1200, step=10,
                value=int(float(settings.get("session_max_seconds", "180"))),
            ).props("label-always")

            session_min.on_value_change(lambda e: db.set_setting("session_min_seconds", str(e.value)))
            session_max.on_value_change(lambda e: db.set_setting("session_max_seconds", str(e.value)))

        # ---- like probability ----
        with ui.card().classes("w-full"):
            ui.label("Like probability").classes("text-lg font-bold")
            ui.label("Chance to like a visible tweet on each scroll tick")
            like_slider = ui.slider(
                min=0.0, max=0.5, step=0.01,
                value=float(settings.get("like_probability", "0.10")),
            ).props("label-always")
            like_slider.on_value_change(lambda e: db.set_setting("like_probability", str(e.value)))

        # ---- concurrency ----
        with ui.card().classes("w-full"):
            ui.label("Concurrency").classes("text-lg font-bold")
            ui.label("How many accounts can warm up at the same time (keep at 1 for safety)")
            concurrent = ui.slider(
                min=1, max=5, step=1,
                value=int(settings.get("max_concurrent", "1")),
            ).props("label-always")
            concurrent.on_value_change(lambda e: db.set_setting("max_concurrent", str(e.value)))

        # ---- adspower api ----
        with ui.card().classes("w-full"):
            ui.label("AdsPower Local API").classes("text-lg font-bold")
            api_input = ui.input(
                label="URL",
                value=settings.get("adspower_api", "http://local.adspower.net:50325"),
            ).classes("w-full")

            def save_api():
                db.set_setting("adspower_api", api_input.value.strip())
                ui.notify("saved", color="positive")
            ui.button("Save", color="primary").on_click(save_api)


# ============================================================================
# AdsPower tab (connection test + profile import)
# ============================================================================
def render_adspower():
    with ui.column().classes("w-full gap-4"):
        ui.label("🦞 AdsPower").classes("text-2xl font-bold")

        status_label = ui.label("Not tested yet").classes("text-lg")
        profiles_area = ui.column().classes("w-full gap-2 mt-2")

        def do_test():
            settings = engine.load_settings()
            client = AdsPowerClient(settings.adspower_api, dry_run=False)
            try:
                ok = client.ping()
                if not ok:
                    status_label.set_text("❌ Cannot reach AdsPower API")
                    status_label.classes(replace="text-lg text-red-500")
                    return
                profiles = client.list_profiles()
                status_label.set_text(f"✅ Connected · {len(profiles)} profile(s)")
                status_label.classes(replace="text-lg text-green-500")

                profiles_area.clear()
                with profiles_area:
                    if not profiles:
                        ui.label("No profiles in AdsPower. Create some first.")
                        return
                    ui.label(f"Found {len(profiles)} profile(s). Click 'Add to pool' to register with a handle.").classes("text-sm text-grey")
                    for p in profiles[:50]:
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(f"{p.get('name', '?')} ").classes("flex-1")
                            ui.label(f"id={p.get('user_id', '?')}").classes("text-sm text-grey flex-1")
                            handle_input = ui.input(placeholder="X handle").classes("flex-1")
                            pid = p.get("user_id", "")
                            pname = p.get("name", "")

                            def mk_add(h_input, profile_id, profile_name):
                                def do():
                                    h = h_input.value.strip().lstrip("@")
                                    if not h:
                                        ui.notify("enter handle first", color="warning")
                                        return
                                    inserted = db.upsert_account(h, profile_id, "adspower", notes=f"from wizard: {profile_name}")
                                    ui.notify(f"{'added' if inserted else 'updated'} @{h}", color="positive")
                                    h_input.set_value("")
                                return do

                            ui.button("Add to pool", color="primary").on_click(mk_add(handle_input, pid, pname))
            except Exception as e:
                status_label.set_text(f"❌ Error: {e}")
                status_label.classes(replace="text-lg text-red-500")

        ui.button("Test connection + list profiles", color="primary").on_click(do_test)


# ============================================================================
# Main page
# ============================================================================
@ui.page("/")
def main_page():
    ui.dark_mode().enable()
    with ui.header().classes("bg-primary"):
        ui.label("🦞 X Warmup Skill · Control Panel").classes("text-xl font-bold text-white")

    with ui.tabs().classes("w-full") as tabs:
        t_dash = ui.tab("Dashboard", icon="dashboard")
        t_acc = ui.tab("Accounts", icon="group")
        t_set = ui.tab("Settings", icon="settings")
        t_ads = ui.tab("AdsPower", icon="link")

    with ui.tab_panels(tabs, value=t_dash).classes("w-full"):
        with ui.tab_panel(t_dash):
            render_dashboard()
        with ui.tab_panel(t_acc):
            render_accounts()
        with ui.tab_panel(t_set):
            render_settings()
        with ui.tab_panel(t_ads):
            render_adspower()


# ============================================================================
# Start
# ============================================================================
if __name__ in {"__main__", "__mp_main__"}:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    print()
    print("🦞 X Warmup Skill · GUI Control Panel")
    print("=====================================")
    print("Opening at http://localhost:8080")
    print("Close this terminal to stop the panel.")
    print()

    ui.run(
        host="127.0.0.1",
        port=8080,
        title="X Warmup Control",
        favicon="🦞",
        reload=False,
        show=True,
    )
