import time
import uuid
import random
import hashlib
import string
from typing import Dict, Any

class RequestSigner:
    """
    Generates dynamic device tokens, timestamps, UUIDs, nonces,
    and cryptographic signatures required by modern mobile and web APIs.
    """
    @staticmethod
    def generate_device_identifiers() -> Dict[str, str]:
        dev_uuid = str(uuid.uuid4())
        dev_id_raw = f"{dev_uuid}-{time.time()}"
        dev_id_md5 = hashlib.md5(dev_id_raw.encode()).hexdigest()
        
        # Simulated IMEI (15 digits with valid Luhn checksum pattern)
        imei_base = "86" + "".join([str(random.randint(0, 9)) for _ in range(12)])
        imei = imei_base + str(random.randint(0, 9))
        
        # Google Advertising ID (GAID) format
        gaid = str(uuid.uuid4())

        now = time.time()
        ts_sec = str(int(now))
        ts_ms = str(int(now * 1000))
        nonce = "".join(random.choices(string.ascii_letters + string.digits, k=16))

        return {
            "uuid": dev_uuid,
            "device_id": dev_id_md5,
            "imei": imei,
            "gaid": gaid,
            "timestamp": ts_sec,
            "timestamp_ms": ts_ms,
            "nonce": nonce
        }

    @staticmethod
    def compute_signature(formula: str, data: Dict[str, Any]) -> str:
        """
        Calculates signatures like:
        formula="md5:{phone}:{timestamp}:SECRET_KEY"
        formula="sha256:{phone}:{nonce}"
        """
        if not formula or ":" not in formula:
            return ""

        parts = formula.split(":")
        algo = parts[0].lower()
        template_raw = ":".join(parts[1:])
        
        rendered = template_raw
        for k, v in data.items():
            rendered = rendered.replace(f"{{{k}}}", str(v))

        raw_bytes = rendered.encode("utf-8")
        if algo == "md5":
            return hashlib.md5(raw_bytes).hexdigest()
        elif algo == "sha256":
            return hashlib.sha256(raw_bytes).hexdigest()
        elif algo == "sha1":
            return hashlib.sha1(raw_bytes).hexdigest()
        return rendered
