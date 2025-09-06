
from __future__ import annotations
from typing import List
def atr_rma(high: List[float], low: List[float], close: List[float], period: int = 14) -> List[float]:
    if not close:
        return []
    trs: List[float] = []
    for i in range(len(close)):
        if i == 0:
            trs.append(high[i]-low[i])
        else:
            tr = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
            trs.append(tr)
    out: List[float] = []
    avg = trs[0]
    for i, v in enumerate(trs):
        if i == 0:
            avg = v
        else:
            avg = (avg*(period-1)+v)/period
        out.append(avg)
    return out
