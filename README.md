# ⚡ PayomboyCallBomber (Next-Gen Red Team Engine)

**PayomboyCallBomber** is an advanced, high-performance stress-testing and verification security engine built for Red Team simulations, telephony rate-limit testing, and defensive auditing.

---

## 🛡️ Anti-Bot & Bypass Engineering Implementations

| Challenge Vector | Legacy Tools (TBomb/Beast) | PayomboyCallBomber |
|---|---|---|
| **TLS Fingerprinting (JA3/JA4)** | OpenSSL Python signature (403/Cloudflare block) | `curl_cffi` Chrome124 TLS handshake & ALPN impersonation |
| **I/O Concurrency** | Blocking Python threads / loops | Non-blocking `asyncio` event loop with semaphore bursts |
| **Request Signing** | None (Static payloads only) | `RequestSigner` with UUID, MD5, timestamp_ms, IMEI, GAID, nonce |
| **WAF Timing Analysis** | Fixed delay loops (easily flagged) | Micro-jitter & randomized wave pacing |
| **Rate-Limit (429/403)** | Keeps spamming dead endpoint | Adaptive exponential backoff per provider |
| **API Rot / Maintenance** | Manual JSON editing | Built-in Health Audit & Auto-Pruning into `verified_providers.json` |
| **CAPTCHA / Turnstile** | Hard fail | `CaptchaSolverBridge` integration with local solvers |

---

## 📁 Architecture Overview

```
PayomboyCallBomber/
├── config/
│   ├── providers.json          # Master list of Call and SMS OTP endpoints
│   ├── verified_providers.json # Auto-curated pool of verified alive endpoints
│   └── settings.json           # Global engine defaults
├── core/
│   ├── engine.py               # Asynchronous stealth execution engine
│   ├── phone.py                # Smart phone number normalizer
│   ├── provider.py             # Request builder with adaptive rate-limit handling
│   ├── signer.py               # Dynamic device token & signature computation
│   ├── captcha.py              # Turnstile & CAPTCHA solver bridge
│   ├── exporter.py             # Automatic verified provider exporter
│   ├── proxy.py                # Rotating HTTP / SOCKS5 proxy manager
│   └── user_agents.py          # Browser fingerprint and realistic headers
├── ui/
│   ├── banner.py               # Terminal banner and console branding
│   └── dashboard.py            # Live status badges, latency tracker, summary
├── proxies.txt                 # Optional rotating proxies
├── requirements.txt            # Project dependencies
└── run.py                      # Interactive wizard and CLI entrypoint
```

---

## 🚀 Quick Start

### 1. Interactive CLI Wizard
```bash
python run.py
```

### 2. Provider Health Audit & Auto-Prune
Benchmark all endpoints against a test target and automatically update the verified pool:
```bash
python run.py --audit --export-verified -t 0812345678
```

### 3. High-Yield Attack on Target (Verified Pool Only)
```bash
python run.py -t 0812345678 -m all -r 2 -c 5 --providers config/verified_providers.json
```

---

## ⚙️ Adding Signed Mobile App Endpoints

To target or audit endpoints that require signature hashing, configure `signature_rule`:
```json
{
  "name": "Target App API",
  "type": "sms",
  "country": "th",
  "method": "POST",
  "url": "https://api.example.com/v1/auth/otp",
  "signature_rule": "md5:{phone}:{timestamp}:SECRET_SALT_HERE",
  "headers": {
    "X-Device-Id": "{device_id}",
    "X-Timestamp": "{timestamp}",
    "X-Signature": "{signature}"
  },
  "body_type": "json",
  "payload": {
    "phone": "{target_intl}"
  },
  "timeout": 8.0,
  "cooldown": 60.0
}
```
Available template variables:
- `{target}`: `0812345678`
- `{target_clean}`: `812345678`
- `{target_intl}`: `66812345678`
- `{target_e164}`: `+66812345678`
- `{device_id}`: MD5 device hash
- `{uuid}`: UUIDv4
- `{imei}`: 15-digit simulated IMEI
- `{gaid}`: Google Advertising ID
- `{timestamp}`: Unix epoch in seconds
- `{timestamp_ms}`: Unix epoch in milliseconds
- `{nonce}`: 16-character alphanumeric string
- `{signature}`: Evaluated signature from `signature_rule`
