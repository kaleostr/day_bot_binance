
from __future__ import annotations
import asyncio
import json
import websockets
from typing import List, Callable, Awaitable

def build_combined_stream_url(base_ws: str, symbols: List[str]) -> str:
    streams = []
    for s in symbols:
        lo = s.lower()
        streams += [f"{lo}@kline_5m", f"{lo}@kline_15m", f"{lo}@kline_1h"]
    stream_path = "/".join(streams)
    if base_ws.endswith("/"):
        return base_ws + f"stream?streams={stream_path}"
    return base_ws + f"/stream?streams={stream_path}"

async def ws_consume(url: str, on_kline_closed: Callable[[str, str, dict], Awaitable[None]]) -> None:
    backoff = 1
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_queue=2048) as ws:
                backoff = 1
                async for raw in ws:
                    msg = json.loads(raw)
                    if "data" not in msg: 
                        continue
                    data = msg["data"]
                    if "k" in data:
                        k = data["k"]
                        if not k.get("x"):
                            continue
                        symbol = data["s"]
                        interval = k["i"]
                        await on_kline_closed(symbol, interval, k)
        except Exception:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
