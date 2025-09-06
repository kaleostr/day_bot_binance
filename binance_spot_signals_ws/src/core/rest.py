
from __future__ import annotations
import httpx
from typing import List, Dict, Any
from ..data.candle import Candle

class BinanceREST:
    def __init__(self, base_url: str = "https://api.binance.com") -> None:
        self.base = base_url
        self.client = httpx.AsyncClient(base_url=self.base, timeout=30.0)

    async def klines(self, symbol: str, interval: str, limit: int = 300) -> List[Candle]:
        r = await self.client.get("/api/v3/klines", params={"symbol": symbol.upper(), "interval": interval, "limit": limit})
        r.raise_for_status()
        arr = r.json()
        out: List[Candle] = []
        for k in arr:
            out.append(Candle(
                open_time=k[0], open=float(k[1]), high=float(k[2]), low=float(k[3]), close=float(k[4]), volume=float(k[5]), close_time=k[6], is_closed=True
            ))
        return out

    async def exchange_info(self, symbols: List[str]) -> Dict[str, Any]:
        import json as _json
        r = await self.client.get("/api/v3/exchangeInfo", params={"symbols": _json.dumps([s.upper() for s in symbols])})
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self.client.aclose()
