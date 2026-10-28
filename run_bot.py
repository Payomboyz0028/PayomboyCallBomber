#!/usr/bin/env python3
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Windows UTF-8 console fix
if sys.platform == "win32":
    try:
        os.system("chcp 65001 > nul 2>&1")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from bot.bot import run_discord_bot

if __name__ == "__main__":
    try:
        run_discord_bot()
    except KeyboardInterrupt:
        print("\n[!] Bot shutdown by operator.")
