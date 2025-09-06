from __future__ import annotations
import os, httpx, asyncio, logging
from typing import Optional
log = logging.getLogger("telegram")

class Telegram:
    def __init__(self, token: Optional[str], chat_id: Optional[str]):
        self.token = token
        self.chat_id = chat_id

    @property
    def available(self)->bool:
        return bool(self.token and self.chat_id)

    @classmethod
    def from_env(cls):
        return cls(os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID"))

    async def send(self, text: str):
        if not self.available:
            log.debug("Telegram not configured, skip")
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        async with httpx.AsyncClient() as c:
            r = await c.post(url, json={"chat_id": self.chat_id, "text": text, "parse_mode":"HTML"})
            try:
                r.raise_for_status()
            except Exception as e:
                log.warning("TG send failed: %s | %s", e, r.text)
