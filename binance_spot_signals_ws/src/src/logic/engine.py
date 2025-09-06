from __future__ import annotations
import logging, math
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np

from src.indicators.impl import ema, macd, rsi, atr_rma, VWAPSession

log = logging.getLogger("engine")

@dataclass
class Series:
    t: List[int] = field(default_factory=list)
    o: List[float] = field(default_factory=list)
    h: List[float] = field(default_factory=list)
    l: List[float] = field(default_factory=list)
    c: List[float] = field(default_factory=list)
    v: List[float] = field(default_factory=list)
    def append(self, k):
        self.t.append(k["t"]); self.o.append(k["o"]); self.h.append(k["h"]); self.l.append(k["l"]); self.c.append(k["c"]); self.v.append(k["v"])
    def arrays(self):
        import numpy as np
        return (np.array(self.t), np.array(self.o), np.array(self.h), np.array(self.l), np.array(self.c), np.array(self.v))

class SignalEngine:
    def __init__(self, tz: ZoneInfo, vwap_reset_local: str, cooldown_minutes: int, min_level: str, tick_size: Dict[str,float], telegram):
        self.tz = tz
        self.vwap_hour, self.vwap_minute = map(int, vwap_reset_local.split(":"))
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.min_level = min_level
        self.tick = tick_size
        self.tg = telegram
        self.h1: Dict[str,Series] = {}
        self.m15: Dict[str,Series] = {}
        self.m5: Dict[str,Series] = {}
        self.vwap: Dict[str,VWAPSession] = {}
        self.last_sent: Dict[str, datetime] = {}

    def warmup(self, sym: str, h1: List[dict], m15: List[dict], m5: List[dict]):
        self.h1[sym] = Series(); self.m15[sym] = Series(); self.m5[sym] = Series()
        for k in h1: self.h1[sym].append(k)
        for k in m15: self.m15[sym].append(k)
        for k in m5: self.m5[sym].append(k)
        self.vwap[sym] = VWAPSession()
        for k in m5:
            if self._is_same_kst_day(k["t"]):
                tp = (k["h"]+k["l"]+k["c"])/3
                self.vwap[sym].update(tp, k["v"])

    def on_close(self, sym: str, interval: str, k: dict):
        if interval == "1h": self.h1[sym].append(k)
        elif interval == "15m": self.m15[sym].append(k)
        elif interval == "5m":
            self.m5[sym].append(k)
            if self._is_session_reset(k["t"]):
                self.vwap[sym].reset()
            tp = (k["h"]+k["l"]+k["c"])/3
            self.vwap[sym].update(tp, k["v"])

    def _is_same_kst_day(self, ts:int)->bool:
        dt = datetime.fromtimestamp(ts, self.tz)
        now = datetime.now(self.tz)
        return dt.date() == now.date()

    def _is_session_reset(self, ts:int)->bool:
        dt = datetime.fromtimestamp(ts, self.tz)
        return dt.hour==self.vwap_hour and dt.minute==self.vwap_minute

    def _round(self, sym:str, price:float)->float:
        step = self.tick.get(sym, 0.0001)
        prec = max(0, -int(round(math.log10(step))))
        return round(round(price/step)*step, prec)

    def _bias(self, sym: str, last_close: float):
        ema20_h1 = ema(self.h1[sym].arrays()[4], 20)
        ema50_h1 = ema(self.h1[sym].arrays()[4], 50)
        ema200_15 = ema(self.m15[sym].arrays()[4], 200)
        bull = ema20_h1[-1] > ema50_h1[-1] and last_close > ema200_15[-1]
        bear = ema20_h1[-1] < ema50_h1[-1] and last_close < ema200_15[-1]
        return bull, bear

    def evaluate(self, sym: str)->str|None:
        t,o,h,l,c,v = self.m5[sym].arrays()
        if len(c) < 60: return None
        bull, bear = self._bias(sym, c[-1])
        if not (bull or bear):
            return None
        _,_,hist = macd(c); rsi14 = rsi(c, 14)
        cond3 = (hist[-2] < 0 <= hist[-1]) if bull else (hist[-2] > 0 >= hist[-1])
        cond3 = cond3 and ((rsi14[-1] >= 50) if bull else (rsi14[-1] <= 50))
        sma20 = np.nanmean(v[-20:]) if len(v)>=20 else np.nanmean(v)
        cond4 = v[-1] > 1.5 * sma20
        trig_high, trig_low = h[-1], l[-1]
        vwap_val = self.vwap[sym].vwap()
        s1p, s2p, s1n, s2n = self.vwap[sym].sigma()
        if bull: cond2 = not np.isnan(vwap_val) and c[-1] >= (s1n if not np.isnan(s1n) else vwap_val)
        else:    cond2 = not np.isnan(vwap_val) and c[-1] <= (s1p if not np.isnan(s1p) else vwap_val)
        score = sum([cond2, cond3, cond4])
        level = "aggressive"
        if score >= 2: level = "base"
        if score == 3: level = "conservative"
        order = {"aggressive":0,"base":1,"conservative":2}
        if order[level] < order.get(self.min_level,2):
            return None
        key = f"{sym}:{'LONG' if bull else 'SHORT'}"
        now = datetime.now(timezone.utc)
        last = self.last_sent.get(key)
        if last and (now - last) < self.cooldown:
            return None
        direction = "LONG" if bull else "SHORT"; side = 1 if bull else -1
        atr14 = atr_rma(h,l,c,14)
        entry = (trig_high * 1.0001) if bull else (trig_low * 0.9999)
        sl = (min(l[-5:]) - 1.2*atr14[-1]) if bull else (max(h[-5:]) + 1.2*atr14[-1])
        R = abs(entry - sl); tp1 = entry + side*R; tp2 = entry + side*2*R
        entry = self._round(sym, entry); sl = self._round(sym, sl); tp1 = self._round(sym, tp1); tp2 = self._round(sym, tp2)
        emoji = {"aggressive":"🟠","base":"🟡","conservative":"🟢"}[level]
        reason = []
        if cond2: reason.append("VWAP confluence")
        if cond3: reason.append("MACD flip + RSI")
        if cond4: reason.append("Volume spike")
        msg = (f"{emoji} {level.title()} | {sym} 5m — {direction}\n"
               f"Вход: {entry}\nSL: {sl}\nTP1: {tp1} | TP2: {tp2}\n"
               f"{' + '.join(reason) if reason else 'Setup'}")
        self.last_sent[key] = now
        return msg

    def status_snapshot(self, symbols: List[str], tz_name: str)->str:
        out = [f"Symbols: {symbols}", f"TZ: {tz_name}", f"Min level: {self.min_level}", f"Cooldown: {self.cooldown}"]
        return "Status:\n" + "\n".join(out)