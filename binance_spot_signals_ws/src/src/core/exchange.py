from __future__ import annotations
import asyncio, json, math, logging
from typing import Dict, List, AsyncGenerator
import httpx, websockets

logger = logging.getLogger("exchange")

class BinanceREST:
    def __init__(self, base: str):
        self.base = base
        self.client = httpx.AsyncClient(base_url=base, timeout=20.0)

    async def get_klines(self, symbol: str, interval: str, limit: int):
        r = await self.client.get("/api/v3/klines", params={"symbol": symbol, "interval": interval, "limit": limit})
        r.raise_for_status()
        out = []
        for it in r.json():
            # [ openTime, open, high, low, close, vol, closeTime, ... , numTrades, takerBuyBaseVol ]
            out.append({
                "t": int(it[6])//1000,  # close time (s)
                "o": float(it[1]), "h": float(it[2]), "l": float(it[3]), "c": float(it[4]),
                "v": float(it[5])
            })
        return out

    async def get_tick_size_map(self, symbols: List[str]):
        r = await self.client.get("/api/v3/exchangeInfo", params={"symbols": json.dumps(symbols)})
        r.raise_for_status()
        data = r.json()["symbols"]
        tick = {}
        for s in data:
            step = None
            for f in s.get("filters", []):
                if f["filterType"] == "PRICE_FILTER":
                    step = float(f["tickSize"]); break
            tick[s["symbol"]] = step or 0.0001
        return tick

class BinanceWS:
    def __init__(self, ws_base: str, symbols: List[str]):
        self.ws_base = ws_base.rstrip("/")
        self.symbols = symbols

    def _streams(self):
        parts = []
        for s in self.symbols:
            ls = s.lower()
            parts += [f"{ls}@kline_1h", f"{ls}@kline_15m", f"{ls}@kline_5m"]
        return "/stream?streams=" + "/".join(parts)

    async def stream(self) -> AsyncGenerator[dict,None]:
        url = f"{self.ws_base}{self._streams()}"
        while True:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
                    logger.info("WS connected: %s", url)
                    async for msg in ws:
                        data = json.loads(msg)
                        if "data" not in data: 
                            continue
                        k = data["data"]["k"]
                        if not k["x"]:
                            continue
                        yield {
                            "type": "kline_close",
                            "symbol": k["s"],
                            "interval": k["i"],
                            "kline": {
                                "t": int(k["T"])//1000,
                                "o": float(k["o"]), "h": float(k["h"]), "l": float(k["l"]), "c": float(k["c"]),
                                "v": float(k["v"])
                            }
                        }
            except Exception as e:
                logger.warning("WS error: %s. Reconnecting in 3s...", e)
                await asyncio.sleep(3)
