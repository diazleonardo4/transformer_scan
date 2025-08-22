# webhook.py
import json, time
from typing import Dict, Any
import requests

def post_webhook(url: str, payload: Dict[str, Any], max_attempts: int = 5) -> bool:
    """
    Send JSON payload to webhook. Retry with backoff if it fails.
    """
    raw = json.dumps(payload, ensure_ascii=False).encode()
    headers = {"Content-Type": "application/json"}
    backoff = 1.0

    for _ in range(max_attempts):
        try:
            r = requests.post(url, headers=headers, data=raw, timeout=20)
            if 200 <= r.status_code < 300:
                return True
        except requests.RequestException:
            pass
        time.sleep(backoff)
        backoff = min(backoff * 2, 30)
    return False
