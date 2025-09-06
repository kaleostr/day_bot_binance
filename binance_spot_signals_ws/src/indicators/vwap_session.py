
from __future__ import annotations
from typing import List, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

class VWAPSession:
    def __init__(self, tz_name: str = "Asia/Seoul") -> None:
        self.tz = ZoneInfo(tz_name)
        self.reset_epoch = None
        self.sum_pv = 0.0
        self.sum_v = 0.0
        self.prices: List[float] = []
        self.volumes: List[float] = []

    def session_key(self, dt_utc: datetime) -> Tuple[int,int,int]:
        kst = dt_utc.astimezone(self.tz)
        return (kst.year, kst.month, kst.day)

    def maybe_reset(self, dt_utc: datetime) -> None:
        key = self.session_key(dt_utc)
        if self.reset_epoch != key:
            self.reset_epoch = key
            self.sum_pv = 0.0
            self.sum_v = 0.0
            self.prices = []
            self.volumes = []

    def update(self, price: float, volume: float, dt_utc: datetime):
        self.maybe_reset(dt_utc)
        self.sum_pv += price * volume
        self.sum_v += volume
        self.prices.append(price)
        self.volumes.append(volume)
        vwap = self.sum_pv / self.sum_v if self.sum_v > 0 else price
        mean = vwap
        if len(self.prices) > 1:
            var = sum((p - mean)**2 for p in self.prices) / (len(self.prices)-1)
            sigma = var ** 0.5
        else:
            sigma = 0.0
        return vwap, sigma
