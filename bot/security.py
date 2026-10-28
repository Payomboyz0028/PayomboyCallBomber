import re
import time
from typing import Optional, Tuple
import discord
from bot.config import BotConfig

# Strict phone regex: E.164 or national format (e.g. 0812345678, +66812345678, 66812345678)
PHONE_REGEX = re.compile(r"^\+?[0-9]{8,15}$")

# Disallowed extensions (anti-malware file dropper guard)
MALICIOUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".ps1", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".py", ".pyw", ".dll", ".sys", ".sh", ".bash", ".apk",
    ".jar", ".msi", ".iso", ".dmg", ".elf", ".bin", ".zip", ".rar", ".7z", ".tar", ".gz"
}

# Forbidden command injection keywords
INJECTION_PATTERNS = re.compile(r"[;`&|\$\{\}\<\>\\\"']|\b(exec|eval|system|rm|del|powershell|cmd|sh|bash)\b", re.IGNORECASE)

class SecurityGuard:
    _user_cooldowns = {}
    _is_busy = False
    _active_target = None

    @classmethod
    def is_authorized(cls, interaction: discord.Interaction) -> bool:
        """
        Validates whether the user is authorized to execute security commands.
        Checks:
        1. Explicit ADMIN_USER_IDS in .env
        2. Discord Guild Owner
        3. User has Administrator permission
        4. User possesses an ALLOWED_ROLE_ID
        """
        user = interaction.user
        
        # Guild Owner is always allowed
        if interaction.guild and interaction.guild.owner_id == user.id:
            return True

        # Check explicit whitelist
        if BotConfig.ADMIN_USER_IDS and user.id in BotConfig.ADMIN_USER_IDS:
            return True

        # Check Discord Administrator permission
        if isinstance(user, discord.Member):
            if user.guild_permissions.administrator:
                return True

            # Check allowed role IDs
            if BotConfig.ALLOWED_ROLE_IDS:
                user_role_ids = {r.id for r in user.roles}
                if any(rid in user_role_ids for rid in BotConfig.ALLOWED_ROLE_IDS):
                    return True

        # If no admin IDs are configured in .env, allow DMs, Administrator, Manage Guild, or Manage Channels
        if not BotConfig.ADMIN_USER_IDS and not BotConfig.ALLOWED_ROLE_IDS:
            if not interaction.guild:
                return True
            if isinstance(user, discord.Member) and (
                user.guild_permissions.administrator
                or user.guild_permissions.manage_guild
                or user.guild_permissions.manage_channels
            ):
                return True

        return False

    @classmethod
    def check_cooldown(cls, user_id: int) -> Tuple[bool, float]:
        """
        Returns (is_ready, seconds_remaining)
        """
        now = time.time()
        last_used = cls._user_cooldowns.get(user_id, 0.0)
        remaining = BotConfig.COOLDOWN_SECONDS - (now - last_used)
        if remaining > 0:
            return False, remaining
        return True, 0.0

    @classmethod
    def trigger_cooldown(cls, user_id: int):
        cls._user_cooldowns[user_id] = time.time()

    @classmethod
    def sanitize_phone(cls, raw_phone: str) -> Tuple[bool, str, Optional[str]]:
        """
        Strictly sanitizes and validates phone numbers.
        Returns (is_valid, cleaned_phone, error_message)
        """
        if not raw_phone:
            return False, "", "Phone number cannot be empty."

        clean = raw_phone.strip().replace(" ", "").replace("-", "")
        
        if INJECTION_PATTERNS.search(clean):
            return False, "", "Security Violation: Potential injection sequence detected."

        if not PHONE_REGEX.match(clean):
            return False, "", "Invalid phone number format. Allowed: 8-15 digits (e.g. 0812345678 or +66812345678)."

        return True, clean, None

    @classmethod
    def validate_attack_params(cls, rounds: int, concurrency: int) -> Tuple[int, int]:
        """
        Enforces server hard-limits on rounds and concurrency.
        """
        safe_rounds = max(1, min(rounds, BotConfig.MAX_ROUNDS_LIMIT))
        safe_concurrency = max(1, min(concurrency, BotConfig.MAX_CONCURRENCY_LIMIT))
        return safe_rounds, safe_concurrency

    @classmethod
    def is_engine_busy(cls) -> bool:
        return cls._is_busy

    @classmethod
    def set_engine_state(cls, busy: bool, target: Optional[str] = None):
        cls._is_busy = busy
        cls._active_target = target

    @classmethod
    def get_active_target(cls) -> Optional[str]:
        return cls._active_target

    @classmethod
    def verify_message_attachments(cls, message: discord.Message) -> bool:
        """
        Blocks any message containing executable attachments or suspicious files.
        """
        if not message.attachments:
            return True

        for att in message.attachments:
            ext = "." + att.filename.split(".")[-1].lower() if "." in att.filename else ""
            if ext in MALICIOUS_EXTENSIONS:
                return False
        return True
