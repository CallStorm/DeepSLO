import base64
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

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

    def fetch_scenario_reports(
        self,
        project_id: str,
        start_time_ms: int,
        end_time_ms: int,
        page: int = 1,
        page_size: int = 50,
        status_in: Optional[List[str]] = None,
        trigger_mode_in: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if status_in is None:
            status_in = ["ERROR", "SUCCESS", "FAKE_ERROR", "PENDING"]
        if trigger_mode_in is None:
            trigger_mode_in = ["SCHEDULE"]

        payload = {
            "current": page,
            "pageSize": page_size,
            "sort": {},
            "keyword": "",
            "viewId": "all_data",
            "combineSearch": {
                "searchMode": "AND",
                "conditions": [
                    {
                        "operator": "CONTAINS",
                        "customField": False,
                        "name": "name",
                        "customFieldType": "",
                    },
                    {
                        "value": status_in,
                        "operator": "IN",
                        "customField": False,
                        "name": "status",
                        "customFieldType": "",
                    },
                    {
                        "value": trigger_mode_in,
                        "operator": "IN",
                        "customField": False,
                        "name": "triggerMode",
                        "customFieldType": "",
                    },
                    {
                        "value": [start_time_ms, end_time_ms],
                        "operator": "BETWEEN",
                        "customField": False,
                        "name": "startTime",
                        "customFieldType": "",
                    },
                ],
            },
            "projectId": str(project_id),
            "moduleType": "API_SCENARIO_REPORT",
            "filter": {"integrated": []},
        }
        resp = self.post("/api/report/scenario/page", json=payload)
        resp.raise_for_status()
        return resp.json()


