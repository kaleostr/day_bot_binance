
from __future__ import annotations
from typing import List

def ema(values: List[float], period: int) -> List[float]:
    if period <= 0:
        raise ValueError("period must be > 0")
    if not values:
        return []
    k = 2 / (period + 1)
    out: List[float] = []
    ema_prev = values[0]
    for i, v in enumerate(values):
        if i == 0:
            ema_val = v
        elif i < period:
            ema_prev = (ema_prev * i + v) / (i + 1)
            ema_val = ema_prev
        else:
            ema_val = v * k + ema_prev * (1 - k)
            ema_prev = ema_val
        out.append(ema_val)
    return out
