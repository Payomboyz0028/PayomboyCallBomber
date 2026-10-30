#!/usr/bin/env python3
import os
import sys
import time
import asyncio
from datetime import datetime
from aiohttp import web

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

# Force unbuffered output for real-time logs
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

from bot.config import BotConfig
from bot.bot import bot
from bot.pinger import start_self_pinger

RUN_LOGS = []
START_TIME = time.time()

def log(msg: str):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    RUN_LOGS.append(line)
    if len(RUN_LOGS) > 100:
        RUN_LOGS.pop(0)

# Wire bot logger
original_on_ready = bot.on_ready
async def custom_on_ready():
    await original_on_ready()
    log(f"🟢 [GATEWAY READY] PayomboyBot connected as: {bot.user} (ID: {bot.user.id})")
bot.on_ready = custom_on_ready

async def create_app():
    app = web.Application()

    async def handle_root(request):
        return web.json_response({
            "service": "PayomboyCallBomber",
            "version": "2.5.0",
            "status": "ONLINE" if bot.is_ready() else "CONNECTING",
            "bot_user": str(bot.user) if bot.is_ready() else None,
            "bot_ready": bot.is_ready(),
            "discord_latency_ms": round(bot.latency * 1000, 2) if bot.is_ready() else None,
            "uptime_seconds": round(time.time() - START_TIME, 1),
            "recent_logs": RUN_LOGS[-15:]
        })

    async def handle_health(request):
        return web.json_response({
            "status": "healthy",
            "bot_ready": bot.is_ready(),
            "bot_user": str(bot.user) if bot.is_ready() else None
        })

    async def handle_logs(request):
        return web.Response(text="\n".join(RUN_LOGS), content_type="text/plain")

    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/ping", handle_health)
    app.router.add_get("/logs", handle_logs)
    return app

async def run_bot_task():
    while True:
        try:
            log("[bot_task] Validating credentials and initiating bot.start...")
            BotConfig.validate()
            await bot.start(BotConfig.TOKEN)
        except Exception as e:
            log(f"[bot_task ERROR] Discord Bot encountered error: {type(e).__name__}: {e}")
            log("[bot_task] Waiting 5 seconds before auto-reconnect...")
            await asyncio.sleep(5)

async def main():
    port = int(os.getenv("PORT", "10000"))
    log(f"[*] Initializing PayomboyCallBomber HTTP Health Server on port {port}...")
    
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log(f"[+] HTTP Health Server listening on 0.0.0.0:{port} (Render Ready)")

    # Start Keep-Alive self-pinger
    asyncio.create_task(start_self_pinger(port))

    # Start Discord Bot in same event loop
    asyncio.create_task(run_bot_task())

    # Keep server running forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("[!] Process interrupted by operator.")
