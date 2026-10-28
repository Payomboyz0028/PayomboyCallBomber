import os
import time
import asyncio
from datetime import datetime
from aiohttp import web

START_TIME = time.time()

async def create_web_app(bot):
    app = web.Application()

    async def handle_root(request):
        bot_user = str(bot.user) if bot.is_ready() else "Connecting..."
        latency = round(bot.latency * 1000, 2) if bot.is_ready() else 0
        uptime = round(time.time() - START_TIME, 1)

        data = {
            "service": "PayomboyCallBomber",
            "version": "2.5.0",
            "engine": "Asyncio/curl_cffi Stealth",
            "status": "ONLINE",
            "bot_user": bot_user,
            "discord_latency_ms": latency,
            "uptime_seconds": uptime,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return web.json_response(data)

    async def handle_health(request):
        return web.json_response({
            "status": "healthy",
            "bot_ready": bot.is_ready(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/ping", handle_health)
    return app

async def start_web_server(bot, port: int = 10000):
    try:
        app = await create_web_app(bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"[+] Web Health Server listening on 0.0.0.0:{port} (Render HTTP Endpoint Ready)", flush=True)
        return runner
    except Exception as e:
        print(f"[-] Failed to bind Web Server on port {port}: {e}", flush=True)
        return None
