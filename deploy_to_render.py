#!/usr/bin/env python3
"""
PAYOMBOY CALL BOMBER — RENDER.COM AUTOMATED DEPLOYMENT TOOL
Deploys or manages the bot on Render.com via REST API.
API Key: rnd_jyF7yXrSoMYfKIP4YkqOwvMACItJ
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_jyF7yXrSoMYfKIP4YkqOwvMACItJ").strip()
RENDER_API_BASE = "https://api.render.com/v1"

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_owner_id() -> str:
    r = requests.get(f"{RENDER_API_BASE}/owners", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        raise ValueError(f"Failed to fetch Render account: {r.status_code} {r.text}")
    owners = r.json()
    if not owners:
        raise ValueError("No owners found in Render account.")
    owner_id = owners[0]["owner"]["id"]
    owner_name = owners[0]["owner"]["name"]
    print(f"[+] Render Account Authenticated: '{owner_name}' (ID: {owner_id})")
    return owner_id

def list_services():
    r = requests.get(f"{RENDER_API_BASE}/services?limit=20", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()
    return []

def create_render_service(repo_url: str, service_name: str = "payomboy-call-bomber"):
    owner_id = get_owner_id()
    
    # Read environment variables to push to Render
    token = os.getenv("DISCORD_TOKEN", "").strip()
    client_id = os.getenv("DISCORD_CLIENT_ID", "").strip()
    client_secret = os.getenv("DISCORD_CLIENT_SECRET", "").strip()

    payload = {
        "type": "web_service",
        "name": service_name,
        "ownerId": owner_id,
        "repo": repo_url,
        "autoDeploy": "yes",
        "branch": "main",
        "serviceDetails": {
            "env": "python",
            "plan": "free",
            "region": "singapore",
            "healthCheckPath": "/health",
            "numInstances": 1,
            "envSpecificDetails": {
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python run_bot.py"
            },
            "envVars": [
                {"key": "PYTHON_VERSION", "value": "3.11.9"},
                {"key": "PORT", "value": "10000"},
                {"key": "DISCORD_TOKEN", "value": token},
                {"key": "DISCORD_CLIENT_ID", "value": client_id},
                {"key": "DISCORD_CLIENT_SECRET", "value": client_secret},
                {"key": "ALLOWED_CHANNEL_IDS", "value": "1565150107513520179"},
                {"key": "MAX_ROUNDS_LIMIT", "value": "50"},
                {"key": "MAX_CONCURRENCY_LIMIT", "value": "50"},
                {"key": "COOLDOWN_SECONDS", "value": "30"}
            ]
        }
    }

    print(f"[*] Dispatching creation request to Render API for '{service_name}'...")
    r = requests.post(f"{RENDER_API_BASE}/services", headers=HEADERS, json=payload, timeout=15)
    if r.status_code in (200, 201):
        res = r.json()
        srv = res.get("service", res)
        srv_id = srv.get("id")
        dashboard_url = srv.get("dashboardUrl")
        service_url = srv.get("serviceDetails", {}).get("url")
        print("\n" + "=" * 60)
        print("🚀 [SUCCESS] SERVICE CREATED ON RENDER.COM!")
        print(f"   ID:            {srv_id}")
        print(f"   Dashboard:     {dashboard_url}")
        print(f"   Public URL:    {service_url}")
        print(f"   Health Check:  {service_url}/health")
        print("=" * 60 + "\n")
        return srv
    else:
        print(f"[-] Render API Error ({r.status_code}): {r.text}")
        return None

def trigger_deploy(service_id: str):
    r = requests.post(f"{RENDER_API_BASE}/services/{service_id}/deploys", headers=HEADERS, json={}, timeout=10)
    if r.status_code in (200, 201):
        print(f"[+] Deploy triggered successfully for service: {service_id}")
        return r.json()
    else:
        print(f"[-] Failed to trigger deploy: {r.status_code} {r.text}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("⚡ PAYOMBOY CALL BOMBER — RENDER DEPLOYER")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        repo = sys.argv[1]
        name = sys.argv[2] if len(sys.argv) > 2 else "payomboy-call-bomber"
        create_render_service(repo, name)
    else:
        print("\nExisting Services on Render:")
        services = list_services()
        for idx, s in enumerate(services, 1):
            srv = s.get("service", s)
            print(f" {idx}. [{srv.get('id')}] {srv.get('name')} ({srv.get('serviceDetails', {}).get('url')})")
        print("\nUsage to create new service:")
        print("  python deploy_to_render.py <github_repo_url> [service_name]")
