
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Candle:
    open_time: int  # ms since epoch
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int  # ms
    is_closed: bool = True

    @property
    def open_dt(self) -> datetime:
        return datetime.fromtimestamp(self.open_time / 1000, tz=timezone.utc)

    @property
    def close_dt(self) -> datetime:
        return datetime.fromtimestamp(self.close_time / 1000, tz=timezone.utc)

    def body(self) -> float:
        return abs(self.close - self.open)

    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low
