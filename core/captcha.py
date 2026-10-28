import os
import asyncio
from typing import Optional, Dict, Any

try:
    from curl_cffi.requests import AsyncSession
except ImportError:
    AsyncSession = None

class CaptchaSolverBridge:
    """
    Bridge to resolve Cloudflare Turnstile, reCAPTCHA v2/v3, and Geetest tokens.
    Supports local solver servers (turnstile_solver-main) or external solver APIs.
    """
    def __init__(self, solver_url: Optional[str] = None, api_key: Optional[str] = None):
        self.solver_url = solver_url or os.getenv("CAPTCHA_SOLVER_URL", "http://127.0.0.1:5000")
        self.api_key = api_key or os.getenv("CAPTCHA_API_KEY", "")

    async def solve_turnstile(self, page_url: str, sitekey: str) -> Optional[str]:
        """
        Request solved turnstile token from local turnstile solver service
        """
        if not self.solver_url:
            return None

        try:
            from curl_cffi.requests import AsyncSession
            async with AsyncSession() as session:
                resp = await session.post(
                    f"{self.solver_url}/solve",
                    json={"url": page_url, "sitekey": sitekey, "api_key": self.api_key},
                    timeout=15.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("token") or data.get("solution")
        except Exception:
            return None
        return None
