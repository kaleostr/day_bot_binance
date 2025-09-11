import httpx
from typing import Dict, Any, List

BN_PUBLIC = "https://api.binance.com"
TF_MAP = {"5m":"5m","15m":"15m","1h":"1h"}

def _to_bnb_symbol(sym: str) -> str:
    return sym.replace("-", "")

def _to_dash_symbol(sym: str) -> str:
    if sym.endswith("USDT"):
        return sym[:-4] + "-USDT"
    return sym

class KucoinClient:
    """Binance-backed client preserving original interface."""
    def __init__(self):
        self._http = httpx.AsyncClient(timeout=15)

    async def fetch_all_tickers(self) -> Dict[str, Any]:
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/ticker/24hr")
        r.raise_for_status()
        arr = r.json()
        tickers = []
        for t in arr:
            sym = str(t.get("symbol",""))
            if any(x in sym for x in ["UP","DOWN","BULL","BEAR"]) and sym.endswith("USDT"):
                continue
            dash = _to_dash_symbol(sym)
            quote_vol = t.get("quoteVolume","0")
            tickers.append({"symbol": dash, "volValue": str(quote_vol)})
        return {"data": {"ticker": tickers}}

    async def fetch_candles(self, symbol: str, tf: str="5m", limit: int=300) -> List[List[Any]]:
        bnb_sym = _to_bnb_symbol(symbol)
        itv = TF_MAP.get(tf, tf)
        params = {"symbol": bnb_sym, "interval": itv, "limit": min(int(limit), 1000)}
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/klines", params=params)
        r.raise_for_status()
        raw = r.json()[-limit:]
        out = []
        for k in raw:
            open_time = int(k[0]); o = float(k[1]); h = float(k[2]); l = float(k[3]); c = float(k[4]); v = float(k[5])
            out.append([open_time, o, c, h, l, v])
        return out

    async def fetch_level1(self, symbol: str) -> Dict[str, Any]:
        bnb_sym = _to_bnb_symbol(symbol)
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/ticker/bookTicker", params={"symbol": bnb_sym})
        r.raise_for_status()
        j = r.json()
        return {"bestBid": str(j.get("bidPrice","0")), "bestAsk": str(j.get("askPrice","0"))}

    async def close(self):
        await self._http.aclose()
