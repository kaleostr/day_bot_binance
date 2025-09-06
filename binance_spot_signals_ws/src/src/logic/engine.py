from __future__ import annotations
import logging, math
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
        self.last_sent: Dict[str,tuple] = {}  # (dir, last_trigger_ts)

    def warmup(self, sym: str, h1: List[dict], m15: List[dict], m5: List[dict]):
        self.h1[sym] = Series(); self.m15[sym] = Series(); self.m5[sym] = Series()
        for k in h1: self.h1[sym].append(k)
        for k in m15: self.m15[sym].append(k)
        for k in m5: self.m5[sym].append(k)
        self.vwap[sym] = VWAPSession()
        # seed VWAP using today's m5 closes from KST midnight
        from datetime import datetime, timezone
        for k in m5:
            if self._is_same_kst_day(k["t"]):
                tp = (k["h"]+k["l"]+k["c"])/3
                self.vwap[sym].update(tp, k["v"])

    def on_close(self, sym: str, interval: str, k: dict):
        if interval == "1h": self.h1[sym].append(k)
        elif interval == "15m": self.m15[sym].append(k)
        elif interval == "5m":
            self.m5[sym].append(k)
            # VWAP session reset at KST 00:00
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

    def evaluate(self, sym: str)->str|None:
        # Only on latest 5m close
        t,o,h,l,c,v = self.m5[sym].arrays()
        if len(c) < 60: return None
        # Indicators
        ema20_h1 = ema(self.h1[sym].arrays()[4], 20)
        ema50_h1 = ema(self.h1[sym].arrays()[4], 50)
        ema200_15 = ema(self.m15[sym].arrays()[4], 200)
        macd_line, signal_line, hist = macd(c)
        rsi14 = rsi(c, 14)
        atr14 = atr_rma(h,l,c,14)
        # Bias
        bull = ema20_h1[-1] > ema50_h1[-1] and c[-1] > ema200_15[-1]
        bear = ema20_h1[-1] < ema50_h1[-1] and c[-1] < ema200_15[-1]
        if not (bull or bear):
            return None
        # Momentum/trigger checks on last 5m candle
        cond3 = (hist[-2] < 0 <= hist[-1]) if bull else (hist[-2] > 0 >= hist[-1])
        cond3 = cond3 and ((rsi14[-1] >= 50) if bull else (rsi14[-1] <= 50))
        # Volume spike
        vol = v
        if len(vol) >= 20:
            sma20 = np.nanmean(vol[-20:])
        else:
            sma20 = np.nanmean(vol)
        cond4 = vol[-1] > 1.5 * sma20
        # Structure: simple breakout of trigger candle high/low
        trig_high, trig_low = h[-1], l[-1]
        # Location: distance to VWAP within 1 sigma
        vwap = self.vwap[sym].vwap()
        s1p, s2p, s1n, s2n = self.vwap[sym].sigma()
        cond2 = False
        if bull and not (np.isnan(s1p) or np.isnan(vwap)):
            cond2 = c[-1] >= s1n  # near/above vwap
        if bear and not (np.isnan(s1n) or np.isnan(vwap)):
            cond2 = c[-1] <= s1p

        # Confirmation level
        score_3to5 = sum([cond3, cond4, True])  # include structure check later
        # Entry/SL/TP
        direction = "LONG" if bull else "SHORT"
        side = 1 if bull else -1
        entry = (trig_high * 1.0001) if bull else (trig_low * 0.9999)
        sl = (min(l[-5:]) - 1.2*atr14[-1]) if bull else (max(h[-5:]) + 1.2*atr14[-1])
        R = abs(entry - sl)
        tp1 = entry + side*R
        tp2 = entry + side*2*R

        entry = self._round(sym, entry)
        sl = self._round(sym, sl)
        tp1 = self._round(sym, tp1)
        tp2 = self._round(sym, tp2)

        # Determine level
        level = None
        if cond3 and cond4 and cond2:
            level = "conservative"
        elif sum([cond3, cond4, cond2])>=2:
            level = "base"
        elif cond3 or cond4:
            level = "aggressive"

        # Cooldown / dedupe
        key = f"{sym}:{direction}"
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if key in self.last_sent:
            d, ts = self.last_sent[key]
            if (now - ts) < self.cooldown:
                return None

        # Respect MIN_ALERT_LEVEL
        order = {"aggressive":0, "base":1, "conservative":2}
        if level is None or order[level] < order.get(self.min_level,2):
            return None

        reason = []
        if cond2: reason.append("VWAP confluence")
        if cond3: reason.append("MACD flip + RSI")
        if cond4: reason.append("Volume spike")

        emoji = {"aggressive":"🟠","base":"🟡","conservative":"🟢"}[level]
        msg = (f"{emoji} {level.title()} | {sym} 5m — {direction}\n"
               f"Вход: {entry}\nSL: {sl}\nTP1: {tp1} | TP2: {tp2}\n"
               f"{' + '.join(reason) if reason else 'Setup'}")
        self.last_sent[key] = (direction, now)
        return msg
