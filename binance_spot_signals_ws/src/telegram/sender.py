
from __future__ import annotations
import httpx
from typing import Optional, List
import asyncio

class TelegramClient:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.base = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=20.0)

    async def send_message(self, text: str) -> None:
        await self.client.post(f"{self.base}/sendMessage", json={"chat_id": self.chat_id, "text": text})

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 10) -> List[dict]:
        r = await self.client.get(f"{self.base}/getUpdates", params={"timeout": timeout, "offset": offset})
        r.raise_for_status()
        return r.json().get("result", [])

    async def close(self) -> None:
        await self.client.aclose()

async def telegram_command_loop(tg: TelegramClient, get_status_text) -> None:
    if tg is None:
        return
    offset = None
    while True:
        try:
            updates = await tg.get_updates(offset=offset, timeout=15)
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                if str(msg.get("chat", {}).get("id")) != str(tg.chat_id):
                    continue
                text = (msg.get("text") or "").strip()
                if text == "/ping":
                    await tg.send_message("pong")
                elif text == "/status":
                    await tg.send_message(get_status_text())
        except Exception:
            await asyncio.sleep(2)
