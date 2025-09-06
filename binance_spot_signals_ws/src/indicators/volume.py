
from __future__ import annotations
from typing import List

def sma(values: List[float], period: int) -> List[float]:
    if not values:
        return []
    out: List[float] = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i-period]
        if i+1 >= period:
            out.append(s/period)
        else:
            out.append(s/(i+1))
    return out
