import httpx
from typing import Dict, Any, List

BN_PUBLIC = "https://api.binance.com"

TF_MAP = {"5m":"5m","15m":"15m","1h":"1h"}

def _to_bnb_symbol(sym: str) -> str:
    # Convert 'SOL-USDT' -> 'SOLUSDT'
    return sym.replace("-", "")

def _to_dash_symbol(sym: str) -> str:
    # Convert 'SOLUSDT' -> 'SOL-USDT' (for display/universe building)
    if sym.endswith("USDT"):
        return sym[:-4] + "-USDT"
    # default: insert dash before last 4 chars (common quote assets could be 3-5 chars, but we mainly use USDT)
    return sym

class KucoinClient:
    """Binance-backed client that preserves the original KuCoin interface used by the app."""
    def __init__(self):
        self._http = httpx.AsyncClient(timeout=15)

    async def fetch_all_tickers(self) -> Dict[str, Any]:
        # Binance 24hr ticker stats for all symbols
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/ticker/24hr")
        r.raise_for_status()
        arr = r.json()
        # Map to KuCoin-like shape: {data: {ticker: [{symbol: 'SOL-USDT', volValue: '...'}]}}
        tickers = []
        for t in arr:
            sym = str(t.get("symbol",""))
            # skip leveraged/ETF-like tokens to keep spot majors
            if any(x in sym for x in ["UP", "DOWN", "BULL", "BEAR"]) and sym.endswith("USDT"):
                continue
            dash = _to_dash_symbol(sym)
            quote_vol = t.get("quoteVolume", "0")  # already in quote units (e.g., USDT)
            tickers.append({"symbol": dash, "volValue": str(quote_vol)})
        return {"data": {"ticker": tickers}}

    async def fetch_candles(self, symbol: str, tf: str = "5m", limit: int = 300) -> List[List[Any]]:
        # Binance klines: [ openTime, open, high, low, close, volume, ... ]
        bnb_sym = _to_bnb_symbol(symbol)
        itv = TF_MAP.get(tf, tf)
        params = {"symbol": bnb_sym, "interval": itv, "limit": min(int(limit), 1000)}
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/klines", params=params)
        r.raise_for_status()
        raw = r.json()
        # Keep chronological order; ensure we only keep the last <limit> rows
        raw = raw[-limit:]
        # Map to KuCoin candle shape: [time(ms), open, close, high, low, volume]
        out = []
        for k in raw:
            open_time = int(k[0])
            open_p = float(k[1]); high_p = float(k[2]); low_p = float(k[3]); close_p = float(k[4])
            vol = float(k[5])
            out.append([open_time, open_p, close_p, high_p, low_p, vol])
        return out

    async def fetch_level1(self, symbol: str) -> Dict[str, Any]:
        bnb_sym = _to_bnb_symbol(symbol)
        r = await self._http.get(f"{BN_PUBLIC}/api/v3/ticker/bookTicker", params={"symbol": bnb_sym})
        r.raise_for_status()
        j = r.json()
        # Map to KuCoin-like keys
        return {"bestBid": str(j.get("bidPrice", "0")), "bestAsk": str(j.get("askPrice", "0"))}

    async def close(self):
        await self._http.aclose()
