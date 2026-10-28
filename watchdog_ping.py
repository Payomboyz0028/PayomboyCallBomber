import os
import sys
import json
import time
import requests
from datetime import datetime

# Windows UTF-8 console fix
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# PAYOMBØYZ RENDER.COM 24/7 AUTO-RESUME & UPTIME WATCHDOG v2.5
# Automated Health Monitor, Keep-Alive Ping & Self-Healing Watchdog
# ==============================================================================

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_jyF7yXrSoMYfKIP4YkqOwvMACItJ").strip()
RENDER_SERVICES_RAW = os.getenv("RENDER_SERVICES_CONFIG", "")
TARGET_PING_URLS_RAW = os.getenv("TARGET_PING_URLS", "")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_services.json")

def send_discord_notification(title, description, color, fields=None):
    """Dispatches a formatted alert embed to the designated Discord Webhook."""
    if not DISCORD_WEBHOOK_URL or "discord.com" not in DISCORD_WEBHOOK_URL:
        print(f"[DISCORD ALERT SKIPPED]: {title} - {description}")
        return

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "footer": {
            "text": "PayomboyZ Render.com Automated Watchdog v2.5",
            "icon_url": "https://payomboyzcreative.online/favicon.ico"
        }
    }
    if fields:
        embed["fields"] = fields

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
        print(f"[DISCORD ALERT SENT]: status={r.status_code}")
    except Exception as e:
        print(f"[WARN] Failed to send Discord webhook: {e}")

def load_target_services(api_key: str):
    """
    Loads target services to monitor.
    Priority order:
    1. RENDER_SERVICES_CONFIG environment variable (JSON)
    2. render_services.json local file
    3. Auto-discovery via Render REST API (pulls all services under account)
    """
    if RENDER_SERVICES_RAW.strip():
        try:
            return json.loads(RENDER_SERVICES_RAW)
        except Exception as e:
            print(f"[ERROR] Failed to parse RENDER_SERVICES_CONFIG secret: {e}")

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to read {CONFIG_FILE}: {e}")

    # Auto-discovery via Render API
    if api_key:
        print("[*] Querying Render REST API for active services...")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        try:
            r = requests.get("https://api.render.com/v1/services?limit=20", headers=headers, timeout=12)
            if r.status_code == 200:
                services_data = r.json()
                discovered = []
                for s in services_data:
                    srv = s.get("service", s)
                    details = srv.get("serviceDetails", {})
                    url = details.get("url", "")
                    health_path = details.get("healthCheckPath", "")
                    full_ping_url = (url.rstrip("/") + (health_path if health_path else "/health")) if url else ""

                    discovered.append({
                        "id": srv.get("id"),
                        "name": srv.get("name"),
                        "type": srv.get("type"),
                        "suspended": srv.get("suspended", "unknown"),
                        "url": url,
                        "ping_url": full_ping_url
                    })
                print(f"[+] Auto-discovered {len(discovered)} services on Render account.")
                return discovered
            else:
                print(f"[-] Render API returned {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"[-] Failed to auto-discover services: {e}")

    # Fallback to default known services
    return [
        {
            "id": "srv-dbh18n5g1s2s73cgh96g",
            "name": "payomboyz-solve-us",
            "type": "web_service",
            "url": "https://payomboyz-solve-us.onrender.com",
            "ping_url": "https://payomboyz-solve-us.onrender.com"
        },
        {
            "id": "srv-dbh11o59fdbs73d92fg0",
            "name": "payomboyz-solve-bot",
            "type": "web_service",
            "url": "https://payomboyz-solve-bot-4co1.onrender.com",
            "ping_url": "https://payomboyz-solve-bot-4co1.onrender.com"
        }
    ]

def check_and_resume_service(api_key: str, service_id: str, service_name: str, current_suspended: str):
    """
    Checks if a service is suspended on Render and triggers an un-suspend / resume operation.
    """
    if not api_key or not service_id:
        return {"action": "skipped", "reason": "No API key or Service ID"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        # Fetch live state from Render
        r = requests.get(f"https://api.render.com/v1/services/{service_id}", headers=headers, timeout=10)
        if r.status_code == 200:
            srv = r.json()
            is_suspended = srv.get("suspended") == "suspended"
            
            if is_suspended or current_suspended == "suspended":
                print(f"  [API] Service '{service_name}' ({service_id}) is SUSPENDED. Triggering RESUME...")
                res = requests.post(f"https://api.render.com/v1/services/{service_id}/resume", headers=headers, json={}, timeout=10)
                if res.status_code in (200, 201, 202):
                    print(f"  [API SUCCESS] Resume request accepted for '{service_name}' ({res.status_code})")
                    return {"action": "resumed", "success": True, "status_code": res.status_code}
                else:
                    print(f"  [API WARN] Resume failed ({res.status_code}): {res.text[:100]}")
                    return {"action": "resume_failed", "success": False, "status_code": res.status_code}
            return {"action": "active", "success": True}
        else:
            return {"action": "check_failed", "status_code": r.status_code}
    except Exception as e:
        print(f"  [API ERROR for {service_name}]: {e}")
        return {"action": "error", "error": str(e)}

def ping_http_endpoint(url: str, timeout: int = 15):
    """
    Sends an HTTP GET request to wake up Render free-tier services and prevent idle sleep.
    """
    if not url:
        return {"status": 0, "latency_ms": 0, "text": "No URL"}

    start_time = time.time()
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PayomboyZ-Watchdog/2.5",
            "Accept": "application/json, text/html, */*"
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        latency = round((time.time() - start_time) * 1000, 2)
        return {
            "status": resp.status_code,
            "latency_ms": latency,
            "text": resp.text[:120].strip()
        }
    except requests.exceptions.Timeout:
        return {"status": 408, "latency_ms": timeout * 1000, "text": "Request Timeout"}
    except Exception as e:
        latency = round((time.time() - start_time) * 1000, 2)
        return {"status": 0, "latency_ms": latency, "text": str(e)[:100]}

def main():
    print("=" * 70)
    print("🚀 PAYOMBØYZ RENDER.COM 24/7 AUTO-RESUME & UPTIME WATCHDOG v2.5")
    print(f"🕒 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)

    services = load_target_services(RENDER_API_KEY)
    print(f"📋 Loaded {len(services)} target services to verify and ping.\n")

    results = []

    for srv in services:
        name = srv.get("name", "Unknown Service")
        srv_id = srv.get("id", "")
        suspended_state = srv.get("suspended", "unknown")
        ping_url = srv.get("ping_url") or srv.get("url")

        print(f"▶ Inspecting: {name} ({srv_id})...")

        # 1. API Resume Check
        api_result = {"action": "none"}
        if srv_id and RENDER_API_KEY:
            api_result = check_and_resume_service(RENDER_API_KEY, srv_id, name, suspended_state)

        # 2. HTTP Keep-Alive Ping
        ping_res = {"status": 0, "latency_ms": 0, "text": "No URL"}
        if ping_url:
            print(f"  -> Sending Keep-Alive Ping to: {ping_url}")
            ping_res = ping_http_endpoint(ping_url)
            print(f"  -> Ping Result: HTTP {ping_res['status']} ({ping_res['latency_ms']}ms)")
            # Also ping /health if not already doing so
            if not ping_url.endswith("/health") and not ping_url.endswith("/ping"):
                health_url = ping_url.rstrip("/") + "/health"
                h_res = ping_http_endpoint(health_url, timeout=5)
                if h_res["status"] == 200:
                    ping_res = h_res

        results.append({
            "name": name,
            "id": srv_id,
            "url": ping_url,
            "api_result": api_result,
            "ping_result": ping_res
        })

    # Extra Standalone Target URLs (if configured)
    if TARGET_PING_URLS_RAW:
        for extra_url in [u.strip() for u in TARGET_PING_URLS_RAW.split(",") if u.strip()]:
            print(f"\n▶ Pinging standalone URL: {extra_url}...")
            p_res = ping_http_endpoint(extra_url)
            results.append({
                "name": extra_url.split("//")[-1].split("/")[0],
                "id": "standalone",
                "url": extra_url,
                "api_result": {"action": "standalone"},
                "ping_result": p_res
            })

    # Construct Discord Notification Embed
    summary_fields = []
    overall_healthy = True

    for r in results:
        ping = r["ping_result"]
        api = r["api_result"]
        status_code = ping.get("status", 0)
        latency = ping.get("latency_ms", 0)

        if api.get("action") == "resumed":
            status_badge = "🔄 Auto-Resumed (Woke Up from Suspension)"
        elif status_code in (200, 201, 204, 301, 302):
            status_badge = f"🟢 Online (HTTP {status_code}) — {latency:.0f}ms"
        elif status_code == 408:
            status_badge = "⏳ Cold Starting (Render Spin-up in Progress)"
            overall_healthy = False
        elif status_code == 0:
            status_badge = f"🔴 Offline ({ping.get('text', 'Connection Failed')})"
            overall_healthy = False
        else:
            status_badge = f"⚠️ Warning (HTTP {status_code}) — {latency:.0f}ms"

        summary_fields.append({
            "name": f"⚡ {r['name']}",
            "value": f"**Endpoint:** `{r['url'] or 'N/A'}`\n**Status:** {status_badge}",
            "inline": False
        })

    embed_color = 0x10b981 if overall_healthy else 0xf59e0b

    send_discord_notification(
        title="🤖 PayomboyZ Render.com 24/7 Watchdog Report",
        description=f"Keep-alive watchdog ping executed at `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}` across {len(results)} services.",
        color=embed_color,
        fields=summary_fields
    )

    print("\n" + "=" * 70)
    print("🏁 Watchdog execution cycle completed successfully.")
    print("=" * 70)

if __name__ == "__main__":
    main()
