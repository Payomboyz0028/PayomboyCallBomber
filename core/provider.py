import json
import time
from typing import Dict, Any, List, Optional
from core.phone import PhoneNumber
from core.user_agents import get_realistic_headers
from core.signer import RequestSigner

class Provider:
    def __init__(self, data: Dict[str, Any]):
        self.name: str = data.get("name", "Unknown")
        self.type: str = data.get("type", "sms").lower() # "call" or "sms"
        self.country: str = data.get("country", "th").lower()
        self.method: str = data.get("method", "POST").upper()
        self.url_template: str = data.get("url", "")
        self.headers_template: Dict[str, str] = data.get("headers", {})
        self.body_type: str = data.get("body_type", "json").lower() # "json", "data", "none"
        self.payload_template: Any = data.get("payload", {})
        self.params_template: Dict[str, str] = data.get("params", {})
        self.timeout: float = float(data.get("timeout", 10.0))
        self.base_cooldown: float = float(data.get("cooldown", 15.0))
        self.cooldown: float = self.base_cooldown
        self.success_codes: List[int] = data.get("success_codes", [200, 201, 202, 204])
        self.success_keyword: Optional[str] = data.get("success_keyword", None)
        self.deny_keywords: List[str] = [k.lower() for k in data.get(
            "deny_keywords",
            [
                "rate limit", "ratelimit", "too many", "try again later",
                "invalid phone", "invalid number", "invalid phone number",
                '"success": false', '"success":false', '"ok": false', '"ok":false',
                '"status": "error"', '"status":"error"', "captcha", "challenge",
                "blocked", "forbidden", "not allowed", "suspended",
                "bad request", "bad_request", '"code": 4', '"code":4', '"code": 5', '"code":5',
                '"status": 4', '"status":4', '"status": 0', '"status":0',
                '"error":', '"_error":', 'error_description', 'error_code'
            ],
        )]
        # Layer 3: captcha challenge gate (bridge wired in engine)
        self.captcha_sitekey: Optional[str] = data.get("captcha_sitekey", None)
        self.captcha_page_url: Optional[str] = data.get("captcha_page_url", None)
        self.captcha_field: str = data.get("captcha_field", "captcha_token")
        # Layer 4: session/CSRF preflight (engine fetches cookies before firing)
        self.preflight_url: Optional[str] = data.get("preflight_url", None)
        self.csrf_selectors: List[str] = data.get("csrf_selectors", ["csrf_token", "_token", "authenticity_token"])
        self.signature_rule: Optional[str] = data.get("signature_rule", None)
        self.impersonate: str = data.get("impersonate", "chrome124")
        
        self.last_used: float = 0.0

    def is_ready(self) -> bool:
        """Check if provider is outside cooldown window"""
        return (time.time() - self.last_used) >= self.cooldown

    def mark_used(self):
        self.last_used = time.time()

    def handle_response_code(self, status_code: int):
        """Adaptive cooldown: if rate limited, scale cooldown dynamically with tight ceiling"""
        if status_code in (429, 403):
            self.cooldown = min(self.cooldown * 1.25, 10.0)
        elif status_code in self.success_codes:
            # Gradually restore base cooldown on success
            self.cooldown = max(self.base_cooldown, self.cooldown * 0.9)

    def _replace_vars(self, item: Any, vars_map: Dict[str, str]) -> Any:
        if isinstance(item, str):
            res = item
            for k, v in vars_map.items():
                res = res.replace(f"{{{k}}}", str(v))
            return res
        elif isinstance(item, dict):
            return {self._replace_vars(k, vars_map): self._replace_vars(v, vars_map) for k, v in item.items()}
        elif isinstance(item, list):
            return [self._replace_vars(i, vars_map) for i in item]
        return item

    def build_request(self, phone: PhoneNumber, extra_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Builds executable request arguments (url, method, headers, json/data, params)
        with dynamic device tokens, timestamps, CSRF tokens, and signature rules applied.
        """
        vars_map = phone.to_template_vars()
        device_vars = RequestSigner.generate_device_identifiers()
        vars_map.update(device_vars)
        if extra_vars:
            vars_map.update(extra_vars)

        if self.signature_rule:
            vars_map["signature"] = RequestSigner.compute_signature(self.signature_rule, vars_map)

        url = self._replace_vars(self.url_template, vars_map)
        
        raw_headers = self._replace_vars(self.headers_template, vars_map)
        headers = get_realistic_headers(raw_headers)

        params = self._replace_vars(self.params_template, vars_map) if self.params_template else None

        req_kwargs: Dict[str, Any] = {
            "method": self.method,
            "url": url,
            "headers": headers,
            "timeout": self.timeout
        }
        if params:
            req_kwargs["params"] = params

        if self.method in ("POST", "PUT", "PATCH"):
            rendered_payload = self._replace_vars(self.payload_template, vars_map)
            if self.body_type == "json":
                req_kwargs["json"] = rendered_payload
            elif self.body_type == "data":
                req_kwargs["data"] = rendered_payload

        return req_kwargs

    def is_success(self, status_code: int, response_text: str) -> bool:
        """
        Layer 1: Strict truth validation.
        HTTP status 200 alone NEVER proves delivery.
        Must be:
        1. In allowed success_codes (200, 201)
        2. Non-empty response body
        3. NOT an HTML page (which indicates WAF challenge, 404 fallback, or redirect)
        4. NOT an anti-bot challenge (Alibaba TMD punish, Cloudflare Turnstile, Akamai)
        5. Free of all denial keywords ('rate limit', 'invalid', 'error', 'failed', etc.)
        6. Contain success_keyword if configured.
        """
        if status_code not in self.success_codes:
            return False

        body = (response_text or "").strip()
        if not body:
            return False

        lowered = body.lower()

        # Reject HTML pages pretending to be API responses
        if (
            lowered.startswith("<!doctype")
            or lowered.startswith("<html")
            or "<head>" in lowered
            or "<body>" in lowered
            or "<script>" in lowered
        ):
            return False

        # Reject Alibaba TMD / WAF challenges / punish paths
        if "punish" in lowered or "_____tmd_____" in lowered or "secdata" in lowered:
            return False
        if "cf-mitigated" in lowered or "attention required!" in lowered or "just a moment..." in lowered:
            return False

        # Positive success keyword check
        if self.success_keyword and self.success_keyword.lower() in lowered:
            return True

        # Reject denial keywords
        for bad in self.deny_keywords:
            if bad in lowered:
                return False

        return True


class ProviderLoader:
    @staticmethod
    def load(filepath: str) -> List[Provider]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        providers = []
        for item in data:
            providers.append(Provider(item))
        return providers
