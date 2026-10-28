import os
from typing import List
from dotenv import load_dotenv

# Load .env file from project root
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path)

class BotConfig:
    TOKEN: str = os.getenv("DISCORD_TOKEN", "").strip()
    CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "").strip()
    CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "").strip()
    
    # Security Whitelist
    ADMIN_USER_IDS: List[int] = [
        int(uid.strip()) for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip().isdigit()
    ]
    ALLOWED_ROLE_IDS: List[int] = [
        int(rid.strip()) for rid in os.getenv("ALLOWED_ROLE_IDS", "").split(",") if rid.strip().isdigit()
    ]
    
    # Engine Guardrails
    MAX_ROUNDS_LIMIT: int = int(os.getenv("MAX_ROUNDS_LIMIT", "5"))
    MAX_CONCURRENCY_LIMIT: int = int(os.getenv("MAX_CONCURRENCY_LIMIT", "10"))
    COOLDOWN_SECONDS: int = int(os.getenv("COOLDOWN_SECONDS", "30"))

    @classmethod
    def validate(cls):
        if not cls.TOKEN:
            raise ValueError("DISCORD_TOKEN is missing or empty in .env!")
