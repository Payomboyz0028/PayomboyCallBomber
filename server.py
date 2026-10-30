#!/usr/bin/env python3
import os
import sys
import asyncio
from aiohttp import web

# Unbuffer stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

port = int(os.getenv("PORT", "10000"))

async def health(request):
    return web.json_response({"status": "healthy", "service": "PayomboyCallBomber"})

async def index(request):
    return web.json_response({"status": "online", "message": "PayomboyCallBomber 24/7 Engine"})

async def run_server():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/ping", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[+] HTTP Server listening on port {port}", flush=True)

    # 1. Start Self-Ping Heartbeat task (Anti-Sleep Pinger)
    from bot.pinger import start_self_pinger
    asyncio.create_task(start_self_pinger(port))

    # 2. Launch Discord Bot in background thread
    try:
        from bot.bot import run_discord_bot
        print("[*] Starting Discord Bot background loop...", flush=True)
        # run in thread or separate task
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_discord_bot)
    except Exception as e:
        print(f"[-] Bot execution error: {e}", flush=True)

    # Keep alive forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_server())
