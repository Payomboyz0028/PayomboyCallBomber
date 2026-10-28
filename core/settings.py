import os
import json
from typing import Optional, Dict, Any

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")

class SettingsManager:
    _cached_settings: Optional[Dict[str, Any]] = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._cached_settings is not None:
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
            "active_pool": "verified"
        }
        
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default_data.update(data)
            except Exception:
                pass
        
        cls._cached_settings = default_data
        return cls._cached_settings

    @classmethod
    def save(cls, new_settings: Dict[str, Any]):
        cls._cached_settings = new_settings
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)

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
