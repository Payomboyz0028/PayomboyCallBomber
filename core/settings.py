import os
import json
from typing import Optional, Dict, Any, List

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")

class SettingsManager:
    _cached_settings: Optional[Dict[str, Any]] = None
    _last_mtime: float = 0.0

    @classmethod
    def load(cls) -> Dict[str, Any]:
        current_mtime = os.path.getmtime(SETTINGS_FILE) if os.path.exists(SETTINGS_FILE) else 0.0
        if cls._cached_settings is not None and current_mtime == cls._last_mtime:
            return cls._cached_settings
        
        default_data = {
            "default_country_code": "66",
            "default_concurrency": 5,
            "default_rounds": 1,
            "delay_between_rounds": 0.5,
            "request_timeout": 6.0,
            "rotate_user_agents": True,
            "verify_ssl": False,
            "log_file": "attack.log",
            "output_channel_id": None,
            "active_pool": "verified",
            "active_banner": "card1",
            "allowed_channels": [1565150107513520179]
        }
        
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_data.update(data)
            except Exception:
                pass
        
        cls._last_mtime = current_mtime
        cls._cached_settings = default_data
        return cls._cached_settings

    @classmethod
    def save(cls, new_settings: Dict[str, Any]):
        cls._cached_settings = new_settings
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)
        cls._last_mtime = os.path.getmtime(SETTINGS_FILE) if os.path.exists(SETTINGS_FILE) else 0.0

    @classmethod
    def get_output_channel_id(cls) -> Optional[int]:
        s = cls.load()
        val = s.get("output_channel_id")
        return int(val) if val else None

    @classmethod
    def set_output_channel_id(cls, channel_id: Optional[int]):
        s = cls.load()
        s["output_channel_id"] = channel_id
        cls.save(s)

    @classmethod
    def get_active_pool(cls) -> str:
        s = cls.load()
        return s.get("active_pool", "verified")

    @classmethod
    def set_active_pool(cls, pool_name: str):
        s = cls.load()
        s["active_pool"] = pool_name
        cls.save(s)

    @classmethod
    def get_active_banner(cls) -> str:
        s = cls.load()
        return s.get("active_banner", "card1")

    @classmethod
    def set_active_banner(cls, banner_name: str):
        s = cls.load()
        s["active_banner"] = banner_name
        cls.save(s)

    @classmethod
    def get_allowed_channels(cls) -> List[int]:
        s = cls.load()
        channels = [int(c) for c in s.get("allowed_channels", []) if str(c).isdigit()]
        env_raw = os.getenv("ALLOWED_CHANNEL_IDS", "")
        for c in env_raw.split(","):
            c = c.strip()
            if c.isdigit():
                val = int(c)
                if val not in channels:
                    channels.append(val)
        return channels

    @classmethod
    def add_allowed_channel(cls, channel_id: int):
        s = cls.load()
        channels = [int(c) for c in s.get("allowed_channels", []) if str(c).isdigit()]
        if channel_id not in channels:
            channels.append(channel_id)
            s["allowed_channels"] = channels
            cls.save(s)

    @classmethod
    def remove_allowed_channel(cls, channel_id: int):
        s = cls.load()
        channels = [int(c) for c in s.get("allowed_channels", []) if str(c).isdigit()]
        if channel_id in channels:
            channels.remove(channel_id)
            s["allowed_channels"] = channels
            cls.save(s)

