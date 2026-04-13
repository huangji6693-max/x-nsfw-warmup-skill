"""
gui/app.py · NiceGUI 控制面板（中文版）

启动方式:
    cd gui && python app.py
    # 或: bash scripts/launch_gui.sh

浏览器打开 http://localhost:8080
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from gui import db, engine
    from gui.adspower import BrowserClient
else:
    from . import db, engine
    from .adspower import BrowserClient

try:
    from nicegui import ui, app as nicegui_app
except ImportError:
    print("❌ nicegui 未安装。运行: pip install nicegui")
    sys.exit(1)


db.bootstrap()


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


# ============================================================================
# 仪表盘
# ============================================================================
def render_dashboard():
    with ui.column().classes("w-full gap-4"):
        ui.label("🦞 X 养号 · 仪表盘").classes("text-2xl font-bold")

        counters = {}
        with ui.row().classes("w-full gap-4"):
            for label, key, color in [
                ("总计", "total", "primary"),
                ("运行中", "active", "positive"),
                ("冷却中", "cooldown", "warning"),
                ("影子封禁", "shadow_ban", "negative"),
                ("验证挑战", "challenge", "warning"),
                ("已掉线", "logged_out", "negative"),
            ]:
                with ui.card().classes("w-40"):
                    ui.label(label).classes("text-sm text-grey")
                    counters[key] = ui.label("0").classes(f"text-3xl text-{color} font-bold")

        with ui.row().classes("w-full items-center gap-4 mt-2"):
            run_label = ui.label("状态：已停止").classes("text-lg")
            mode_label = ui.label("模式：模拟运行").classes("text-lg")
            start_btn = ui.button("▶ 启动", color="positive")
            stop_btn = ui.button("■ 停止", color="negative")

        async def do_start():
            db.log_event("操作", "点击了启动")
            await engine.scheduler.start()
            ui.notify("调度器已启动", color="positive")

        async def do_stop():
            db.log_event("操作", "点击了停止")
            await engine.scheduler.stop()
            ui.notify("调度器已停止", color="warning")

        start_btn.on_click(do_start)
        stop_btn.on_click(do_stop)

        ui.label("实时日志").classes("text-lg font-bold mt-4")
        log_widget = ui.log(max_lines=200).classes("w-full h-64 bg-black text-green-400 font-mono text-xs")

        def refresh():
            counts = db.account_counts()
            for k, widget in counters.items():
                widget.set_text(str(counts.get(k, 0)))

            settings = engine.load_settings()
            running = engine.scheduler.is_running()
            run_label.set_text(f"状态：{'运行中 🟢' if running else '已停止 🔴'}")
            mode_label.set_text(f"模式：{'模拟运行 ✅' if settings.dry_run else '真实运行 ⚠️'}")

            new_events = db.events_since(state["last_event_id"], limit=100)
            if new_events:
                for ev in new_events:
                    line = f"{fmt_ts(ev['ts'])}  [{ev['event_type']}]  {ev['detail'] or ''}"
                    log_widget.push(line)
                state["last_event_id"] = new_events[-1]["id"]

        ui.timer(2.0, refresh)
        refresh()


# ============================================================================
# 账号管理
# ============================================================================
def render_accounts():
    with ui.column().classes("w-full gap-4"):
        ui.label("👥 账号管理").classes("text-2xl font-bold")

        accounts_table = ui.table(
            columns=[
                {"name": "handle", "label": "用户名", "field": "handle", "align": "left"},
                {"name": "profile", "label": "浏览器配置 ID", "field": "fingerprint_profile_id", "align": "left"},
                {"name": "browser", "label": "浏览器类型", "field": "fingerprint_browser", "align": "left"},
                {"name": "status", "label": "状态", "field": "status", "align": "left"},
                {"name": "last", "label": "上次养号", "field": "last_warmup_at", "align": "left"},
                {"name": "notes", "label": "备注", "field": "notes", "align": "left"},
            ],
            rows=[],
            row_key="handle",
        ).classes("w-full")

        ui.label("添加账号").classes("text-lg font-bold mt-4")
        with ui.row().classes("w-full gap-2 items-end"):
            new_handle = ui.input(label="X 用户名", placeholder="alice_cute").classes("flex-1")
            new_profile = ui.input(label="浏览器配置 ID", placeholder="abc123def456").classes("flex-1")
            new_browser = ui.select(
                {"bitbrowser": "比特浏览器", "adspower": "AdsPower", "manual": "手动", "patchright": "Patchright"},
                value="bitbrowser",
                label="浏览器类型",
            )
            new_notes = ui.input(label="备注（选填）").classes("flex-1")

            def add_clicked():
                h = new_handle.value.strip().lstrip("@")
                p = new_profile.value.strip()
                if not h or not p:
                    ui.notify("用户名和配置 ID 不能为空", color="warning")
                    return
                inserted = db.upsert_account(h, p, new_browser.value, notes=new_notes.value or "")
                ui.notify(f"{'添加成功' if inserted else '更新成功'} @{h}", color="positive")
                new_handle.set_value("")
                new_profile.set_value("")
                new_notes.set_value("")
                refresh_table()

            ui.button("添加 / 更新", color="primary").on_click(add_clicked)

        ui.label("删除账号").classes("text-lg font-bold mt-4 text-red-500")
        with ui.row().classes("w-full gap-2 items-end"):
            del_handle = ui.input(label="要删除的用户名", placeholder="alice_cute").classes("flex-1")

            def delete_clicked():
                h = del_handle.value.strip().lstrip("@")
                if not h:
                    return
                db.delete_account(h)
                ui.notify(f"已删除 @{h}", color="warning")
                del_handle.set_value("")
                refresh_table()

            ui.button("删除", color="negative").on_click(delete_clicked)

        def refresh_table():
            accounts_table.rows = db.list_accounts()
            accounts_table.update()

        refresh_table()
        ui.timer(5.0, refresh_table)


# ============================================================================
# 设置
# ============================================================================
def render_settings():
    with ui.column().classes("w-full gap-4 max-w-2xl"):
        ui.label("⚙️ 设置").classes("text-2xl font-bold")
        ui.label("修改后自动生效，无需重启").classes("text-sm text-grey")

        settings = db.load_all_settings()

        with ui.card().classes("w-full"):
            ui.label("安全模式").classes("text-lg font-bold")
            dry_run_switch = ui.switch(
                "模拟运行（不会真的操作你的 X 账号）",
                value=settings.get("dry_run", "true").lower() == "true",
            )

            def on_dry_run_change(e):
                db.set_setting("dry_run", "true" if e.value else "false")
                ui.notify(f"模拟运行：{'开启 ✅' if e.value else '关闭 ⚠️ 真实模式'}",
                          color="positive" if e.value else "warning")
            dry_run_switch.on_value_change(on_dry_run_change)

        with ui.card().classes("w-full"):
            ui.label("养号频率").classes("text-lg font-bold")

            ui.label("每个号最少间隔几小时再刷一次")
            interval_min = ui.slider(
                min=0.5, max=24.0, step=0.5,
                value=float(settings.get("interval_min_hours", "4.0")),
            ).props("label-always")

            ui.label("每个号最多间隔几小时再刷一次")
            interval_max = ui.slider(
                min=1.0, max=48.0, step=0.5,
                value=float(settings.get("interval_max_hours", "8.0")),
            ).props("label-always")

            interval_min.on_value_change(lambda e: db.set_setting("interval_min_hours", str(e.value)))
            interval_max.on_value_change(lambda e: db.set_setting("interval_max_hours", str(e.value)))

        with ui.card().classes("w-full"):
            ui.label("单次刷推时长").classes("text-lg font-bold")

            ui.label("最短刷多少秒")
            session_min = ui.slider(
                min=30, max=600, step=10,
                value=int(float(settings.get("session_min_seconds", "120"))),
            ).props("label-always")

            ui.label("最长刷多少秒")
            session_max = ui.slider(
                min=60, max=1200, step=10,
                value=int(float(settings.get("session_max_seconds", "300"))),
            ).props("label-always")

            session_min.on_value_change(lambda e: db.set_setting("session_min_seconds", str(e.value)))
            session_max.on_value_change(lambda e: db.set_setting("session_max_seconds", str(e.value)))

        with ui.card().classes("w-full"):
            ui.label("点赞概率").classes("text-lg font-bold")
            ui.label("每次滚动时有多大概率点赞（只点赞成人内容）")
            like_slider = ui.slider(
                min=0.0, max=0.5, step=0.01,
                value=float(settings.get("like_probability", "0.03")),
            ).props("label-always")
            like_slider.on_value_change(lambda e: db.set_setting("like_probability", str(e.value)))

        with ui.card().classes("w-full"):
            ui.label("同时运行数").classes("text-lg font-bold")
            ui.label("同时能有几个号在刷（建议保持 1，最安全）")
            concurrent = ui.slider(
                min=1, max=5, step=1,
                value=int(settings.get("max_concurrent", "1")),
            ).props("label-always")
            concurrent.on_value_change(lambda e: db.set_setting("max_concurrent", str(e.value)))

        with ui.card().classes("w-full"):
            ui.label("指纹浏览器连接").classes("text-lg font-bold")

            browser_type = ui.select(
                {"bitbrowser": "比特浏览器", "adspower": "AdsPower"},
                value=settings.get("browser_type", "bitbrowser"),
                label="浏览器类型",
            ).classes("w-full")

            api_input = ui.input(
                label="API 地址",
                value=settings.get("browser_api",
                      settings.get("adspower_api", "http://127.0.0.1:54345")),
            ).classes("w-full")

            def save_browser_config():
                db.set_setting("browser_type", browser_type.value)
                db.set_setting("browser_api", api_input.value.strip())
                ui.notify("已保存", color="positive")
            ui.button("保存", color="primary").on_click(save_browser_config)


# ============================================================================
# 指纹浏览器
# ============================================================================
def render_browser():
    with ui.column().classes("w-full gap-4"):
        ui.label("🔗 指纹浏览器").classes("text-2xl font-bold")

        status_label = ui.label("尚未测试连接").classes("text-lg")
        profiles_area = ui.column().classes("w-full gap-2 mt-2")

        def do_test():
            settings = engine.load_settings()
            browser_type = db.get_setting("browser_type", "bitbrowser")
            client = BrowserClient(settings.adspower_api, browser_type=browser_type, dry_run=False)
            try:
                ok = client.ping()
                if not ok:
                    status_label.set_text("❌ 连接失败，请检查指纹浏览器是否打开")
                    status_label.classes(replace="text-lg text-red-500")
                    return
                profiles = client.list_profiles()
                status_label.set_text(f"✅ 连接成功 · 发现 {len(profiles)} 个浏览器窗口")
                status_label.classes(replace="text-lg text-green-500")

                profiles_area.clear()
                with profiles_area:
                    if not profiles:
                        ui.label("指纹浏览器里没有窗口，请先去创建。")
                        return
                    ui.label(f"找到 {len(profiles)} 个窗口。在每个窗口旁边填上对应的 X 用户名，然后点「加入号池」。").classes("text-sm text-grey")
                    for p in profiles[:50]:
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(f"{p.get('name', '?')} ").classes("flex-1")
                            ui.label(f"ID: {p.get('user_id', '?')}").classes("text-sm text-grey flex-1")
                            handle_input = ui.input(placeholder="X 用户名").classes("flex-1")
                            pid = p.get("user_id", "")
                            pname = p.get("name", "")
                            btype = db.get_setting("browser_type", "bitbrowser")

                            def mk_add(h_input, profile_id, profile_name, bt):
                                def do():
                                    h = h_input.value.strip().lstrip("@")
                                    if not h:
                                        ui.notify("请先填写用户名", color="warning")
                                        return
                                    inserted = db.upsert_account(h, profile_id, bt, notes=f"来自: {profile_name}")
                                    ui.notify(f"{'已添加' if inserted else '已更新'} @{h}", color="positive")
                                    h_input.set_value("")
                                return do

                            ui.button("加入号池", color="primary").on_click(mk_add(handle_input, pid, pname, btype))
            except Exception as e:
                status_label.set_text(f"❌ 出错: {e}")
                status_label.classes(replace="text-lg text-red-500")

        ui.button("测试连接 + 获取窗口列表", color="primary").on_click(do_test)


# ============================================================================
# 主页面
# ============================================================================
@ui.page("/")
def main_page():
    ui.dark_mode().enable()
    with ui.header().classes("bg-primary"):
        ui.label("🦞 X 养号工具 · 控制面板").classes("text-xl font-bold text-white")

    with ui.tabs().classes("w-full") as tabs:
        t_dash = ui.tab("仪表盘", icon="dashboard")
        t_acc = ui.tab("账号管理", icon="group")
        t_set = ui.tab("设置", icon="settings")
        t_browser = ui.tab("指纹浏览器", icon="link")

    with ui.tab_panels(tabs, value=t_dash).classes("w-full"):
        with ui.tab_panel(t_dash):
            render_dashboard()
        with ui.tab_panel(t_acc):
            render_accounts()
        with ui.tab_panel(t_set):
            render_settings()
        with ui.tab_panel(t_browser):
            render_browser()


# ============================================================================
# 启动
# ============================================================================
if __name__ in {"__main__", "__mp_main__"}:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    print()
    print("🦞 X 养号工具 · 控制面板")
    print("========================")
    print("浏览器打开 http://localhost:8080")
    print("关闭这个终端窗口 = 停止面板")
    print()

    ui.run(
        host="127.0.0.1",
        port=8080,
        title="X 养号工具",
        favicon="🦞",
        reload=False,
        show=True,
    )
