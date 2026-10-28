import re
from typing import Dict

class PhoneNumber:
    """
    Normalizes phone numbers into all common API formats.
    Specialized for Thailand (+66) while remaining globally compatible.
    """
    def __init__(self, raw_number: str, default_country_code: str = "66"):
        self.raw = str(raw_number).strip()
        self.default_country_code = default_country_code.lstrip("+")
        self.digits = re.sub(r"\D", "", self.raw)
        self.country_code, self.national, self.local = self._parse()

    def _parse(self):
        digits = self.digits
        cc = self.default_country_code
        
        # Check if already starts with country code without plus
        if digits.startswith(cc) and len(digits) > len(cc) + 7:
            national = digits[len(cc):]
            local = f"0{national}"
            return cc, national, local

        # Thai local standard: starts with 0 (e.g. 0812345678 or 021234567)
        if digits.startswith("0") and len(digits) in (9, 10):
            national = digits[1:]
            return cc, national, digits

        # Raw national number without 0 (e.g. 812345678)
        if len(digits) in (8, 9):
            national = digits
            local = f"0{digits}"
            return cc, national, local

        # Fallback generic
        national = digits
        local = f"0{digits}" if not digits.startswith("0") else digits
        return cc, national, local

    @property
    def e164(self) -> str:
        """Format: +66812345678"""
        return f"+{self.country_code}{self.national}"

    @property
    def intl(self) -> str:
        """Format: 66812345678"""
        return f"{self.country_code}{self.national}"

    @property
    def formatted_local(self) -> str:
        """Format: 081-234-5678 or similar"""
        if len(self.local) == 10:
            return f"{self.local[:3]}-{self.local[3:6]}-{self.local[6:]}"
        elif len(self.local) == 9:
            return f"{self.local[:2]}-{self.local[2:5]}-{self.local[5:]}"
        return self.local

    def to_template_vars(self) -> Dict[str, str]:
        """
        Dictionary of variables usable in providers payload/URL templating
        """
        return {
            "target": self.local,               # 0812345678
            "phone": self.local,                # 0812345678
            "target_clean": self.national,      # 812345678
            "phone_clean": self.national,       # 812345678
            "country_code": self.country_code,  # 66
            "target_intl": self.intl,           # 66812345678
            "target_e164": self.e164,           # +66812345678
            "phone_formatted": self.formatted_local # 081-234-5678
        }
