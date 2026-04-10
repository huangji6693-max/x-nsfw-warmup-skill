"""
X Warmup Skill · GUI mode

A local, visual control panel for users who just want to run a simple
scroll-and-like warmup loop on their existing X accounts, without
touching the command line for day-to-day operation.

Architecture:
    gui/db.py         shared SQLite schema + query helpers
    gui/adspower.py   AdsPower Local API wrapper with dry-run support
    gui/engine.py     background scheduler + simplified 2-action set
    gui/app.py        NiceGUI web panel (localhost:8080)

Run with:
    cd gui && python app.py
    # or: bash scripts/launch_gui.sh
"""

__version__ = "0.5.0-gui"
