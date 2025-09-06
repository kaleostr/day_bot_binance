
from __future__ import annotations
from typing import List, Tuple
from .ema import ema

def macd(close: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
    if not close:
        return [], [], []
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    hist = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, hist
