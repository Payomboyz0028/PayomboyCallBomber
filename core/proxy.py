import os
import random
from typing import List, Optional

class ProxyManager:
    """
    Loads and rotates proxies (http, https, socks5).
    """
    def __init__(self, proxy_file: str = "proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies: List[str] = []
        self.load_proxies()

    def load_proxies(self):
        if not os.path.exists(self.proxy_file):
            return
        
        with open(self.proxy_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            
        formatted = []
        for line in lines:
            if not line.startswith(("http://", "https://", "socks5://", "socks4://")):
                line = f"http://{line}"
            formatted.append(line)
        self.proxies = formatted

    def get_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    @property
    def has_proxies(self) -> bool:
        return len(self.proxies) > 0

    @property
    def count(self) -> int:
        return len(self.proxies)
