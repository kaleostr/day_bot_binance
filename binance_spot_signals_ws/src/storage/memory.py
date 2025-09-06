
from __future__ import annotations
from collections import deque
from typing import Deque, Dict, Tuple, List
from ..data.candle import Candle

class TimeSeriesStorage:
    def __init__(self, maxlen: int = 1200) -> None:
        self._data: Dict[Tuple[str, str], Deque[Candle]] = {}
        self.maxlen = maxlen

    def get_series(self, symbol: str, interval: str) -> Deque[Candle]:
        key = (symbol.upper(), interval)
        if key not in self._data:
            self._data[key] = deque(maxlen=self.maxlen)
        return self._data[key]

    def append(self, symbol: str, interval: str, candle: Candle) -> None:
        self.get_series(symbol, interval).append(candle)

    def tail(self, symbol: str, interval: str, n: int) -> List[Candle]:
        dq = self.get_series(symbol, interval)
        return list(dq)[-n:]
