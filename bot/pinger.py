"""
Internal Keep-Alive Pinger for Render Free Tier (Self-Ping Heartbeat).
Pings the service's own URL every 4 minutes to prevent Render from idling.
"""
import os
import asyncio
import httpx
from datetime import datetime

async def start_self_pinger(port: int = 10000):
    await asyncio.sleep(15) # Wait for server boot
    external_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not external_url:
        external_url = f"https://payomboy-call-bomber.onrender.com"

    ping_url = f"{external_url}/health"
    print(f"🛡️ [Anti-Sleep Pinger Active] Self-Heartbeat targeting: {ping_url}", flush=True)

    async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
        while True:
            try:
                r = await client.get(ping_url)
                print(f"⚡ [Anti-Sleep Heartbeat] Ping status HTTP {r.status_code} at {datetime.utcnow().strftime('%H:%M:%S UTC')}", flush=True)
            except Exception as e:
                print(f"⚠️ [Anti-Sleep Notice] Self-ping issue: {e}", flush=True)
            
            # Ping every 4 minutes (Render sleep timeout is 15 minutes)
            await asyncio.sleep(240)

