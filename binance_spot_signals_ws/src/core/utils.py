
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

def build_tick_map(exchange_info: Dict[str, Any]) -> Dict[str, float]:
    out = {}
    for s in exchange_info.get("symbols", []):
        sym = s["symbol"].upper()
        tick = None
        for f in s.get("filters", []):
            if f.get("filterType") == "PRICE_FILTER":
                tick = float(f.get("tickSize"))
                break
        if tick is None:
            tick = 0.00000001
        out[sym] = tick
    return out

def round_to_tick(price: float, tick: float) -> float:
    if tick <= 0:
        return price
    q = Decimal(str(tick))
    p = Decimal(str(price))
    n = (p / q).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return float(n * q)

def pct_diff(a: float, b: float) -> float:
    if b == 0: return 0.0
    return abs(a - b) / b * 100.0
