
from __future__ import annotations
from typing import List

def rma(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    out: List[float] = []
    avg = values[0]
    for i, v in enumerate(values):
        if i == 0:
            avg = v
        else:
            avg = (avg * (period - 1) + v) / period
        out.append(avg)
    return out

def rsi(close: List[float], period: int = 14) -> List[float]:
    if len(close) < 2:
        return [0.0 for _ in close]
    deltas = [close[i] - close[i-1] for i in range(1, len(close))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gains = rma(gains, period)
    avg_losses = rma(losses, period)
    out: List[float] = [0.0]
    for g, l in zip(avg_gains, avg_losses):
        if l == 0:
            val = 100.0
        else:
            rs = g / l
            val = 100 - (100 / (1 + rs))
        out.append(val)
    return out[:len(close)]
