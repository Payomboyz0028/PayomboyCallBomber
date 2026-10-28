import json
import os
from typing import List
from core.provider import Provider

class ProviderExporter:
    @staticmethod
    def export_verified(providers: List[Provider], successful_names: List[str], output_path: str):
        verified = [p for p in providers if p.name in successful_names]
        
        # Serialize back to dictionary format
        serialized = []
        for p in verified:
            item = {
                "name": p.name,
                "type": p.type,
                "country": p.country,
                "method": p.method,
                "url": p.url_template,
                "headers": p.headers_template,
                "body_type": p.body_type,
                "payload": p.payload_template,
                "timeout": p.timeout,
                "cooldown": p.base_cooldown,
                "success_codes": p.success_codes
            }
            if p.params_template:
                item["params"] = p.params_template
            if p.signature_rule:
                item["signature_rule"] = p.signature_rule
            serialized.append(item)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
