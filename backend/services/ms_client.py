import base64
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Any

from Crypto.Cipher import AES
import requests


def _aes_encrypt(text: str, secret_key: str, iv: str) -> bytes:
    bs = AES.block_size

    def pad(s: str) -> str:
        return s + (bs - len(s) % bs) * chr(bs - len(s) % bs)

    cipher = AES.new(secret_key.encode("UTF-8"), AES.MODE_CBC, iv.encode("UTF-8"))
    encrypted = cipher.encrypt(pad(text).encode("UTF-8"))
    return base64.b64encode(encrypted)


def build_headers(ak: str, sk: str) -> Dict[str, str]:
    timestamp_ms = int(round(time.time() * 1000))
    combo_key = f"{ak}|{uuid.uuid4()}|{timestamp_ms}"
    signature = _aes_encrypt(combo_key, sk, ak).decode("UTF-8")
    return {
        "Content-Type": "application/json",
        "ACCEPT": "application/json",
        "accessKey": ak,
        "signature": signature,
        "Connection": "close",
    }


@dataclass
class MSClient:
    base_url: str
    ak: str
    sk: str

    def post(self, path: str, json: Any) -> requests.Response:
        headers = build_headers(self.ak, self.sk)
        url = self.base_url.rstrip("/") + path
        return requests.post(url, json=json, headers=headers, timeout=30)


