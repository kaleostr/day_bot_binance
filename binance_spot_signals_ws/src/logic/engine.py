from __future__ import annotations
import logging, math
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import numpy as np
from zoneinfo import ZoneInfo

from src.indicators.impl import ema, macd, rsi, atr_rma, VWAPSession, supertrend_basic

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

def bullish_engulf(o1,h1,l1,c1, o2,h2,l2,c2)->bool:
    return (c1 < o1) and (c2 > o2) and (o2 <= c1) and (c2 >= o1)

def bearish_engulf(o1,h1,l1,c1, o2,h2,l2,c2)->bool:
    return (c1 > o1) and (c2 < o2) and (o2 >= c1) and (c2 <= o1)

def pin_bar_bull(o,h,l,c)->bool:
    rng = h - l
    return (rng > 0) and ((h - max(c,o)) <= 0.25*rng) and ((min(c,o) - l) >= 0.6*rng)

def pin_bar_bear(o,h,l,c)->bool:
    rng = h - l
    return (rng > 0) and ((min(c,o) - l) <= 0.25*rng) and ((h - max(c,o)) >= 0.6*rng)

def impulse_bull(o,h,l,c)->bool:
    rng = h - l; body = abs(c - o)
    return rng>0 and body/rng >= 0.75 and c>o

def impulse_bear(o,h,l,c)->bool:
    rng = h - l; body = abs(c - o)
    return rng>0 and body/rng >= 0.75 and c<o

def local_level_breakout(high: np.ndarray, low: np.ndarray, lookback:int=10)->Tuple[float,float]:
    if high.size < lookback+2: return (np.nan, np.nan)
    res = np.max(high[-(lookback+2):-2])
    sup = np.min(low[-(lookback+2):-2])
    return (res, sup)

class SignalEngine:
    def __init__(self, tz: ZoneInfo, vwap_reset_local: str, cooldown_minutes: int, min_count: int,
                 tick_size: Dict[str,float], telegram,
                 ema_fast_1h: int=20, ema_slow_1h: int=50, ema_200_15m: int=200,
                 macd_fast: int=12, macd_slow: int=26, macd_signal: int=9,
                 rsi_period: int=14, rsi_zone_low: int=40, rsi_zone_mid: int=50, rsi_zone_high: int=60,
                 atr_period: int=14, atr_sl_mult: float=1.3,
                 vol_sma_period: int=20, vol_spike_mult: float=1.5,
                 supertrend_enabled: bool=False, supertrend_period: int=10, supertrend_multiplier: float=3.0):
        self.tz = tz
        self.vwap_hour, self.vwap_minute = map(int, vwap_reset_local.split(":"))
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.min_count = max(1, min(5, int(min_count)))
        self.tick = tick_size
        self.tg = telegram
        self.h1: Dict[str,Series] = {}
        self.m15: Dict[str,Series] = {}
        self.m5: Dict[str,Series] = {}
        self.vwap: Dict[str,VWAPSession] = {}
        self.last_sent: Dict[str, datetime] = {}
        self.ema_fast_1h = ema_fast_1h; self.ema_slow_1h = ema_slow_1h; self.ema_200_15m = ema_200_15m
        self.macd_fast = macd_fast; self.macd_slow = macd_slow; self.macd_signal = macd_signal
        self.rsi_period = rsi_period
        self.rsi_low = rsi_zone_low; self.rsi_mid = rsi_zone_mid; self.rsi_high = rsi_zone_high
        self.atr_period = atr_period; self.atr_sl_mult = atr_sl_mult
        self.vol_sma_period = vol_sma_period; self.vol_spike_mult = vol_spike_mult
        self.supertrend_enabled = supertrend_enabled
        self.supertrend_period = supertrend_period; self.supertrend_multiplier = supertrend_multiplier

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
        dt = datetime.fromtimestamp(ts, self.tz); now = datetime.now(self.tz)
        return dt.date() == now.date()

    def _is_session_reset(self, ts:int)->bool:
        dt = datetime.fromtimestamp(ts, self.tz)
        return dt.hour==self.vwap_hour and dt.minute==self.vwap_minute

    def _round(self, sym:str, price:float)->float:
        step = self.tick.get(sym, 0.0001)
        prec = max(0, -int(round(math.log10(step))))
        return round(round(price/step)*step, prec)

    def _bias(self, sym: str, last_close: float)->Tuple[bool,bool]:
        ema20_h1 = ema(self.h1[sym].arrays()[4], self.ema_fast_1h)
        ema50_h1 = ema(self.h1[sym].arrays()[4], self.ema_slow_1h)
        ema200_15 = ema(self.m15[sym].arrays()[4], self.ema_200_15m)
        bull = ema20_h1[-1] > ema50_h1[-1] and last_close > ema200_15[-1]
        bear = ema20_h1[-1] < ema50_h1[-1] and last_close < ema200_15[-1]
        return bull, bear

    def _location_vwap(self, sym: str, price: float)->Tuple[bool,bool]:
        vwap_val = self.vwap[sym].vwap()
        s1p, s2p, s1n, s2n = self.vwap[sym].sigma()
        if np.isnan(vwap_val): return (False,False)
        long_ok = price >= (s1n if not np.isnan(s1n) else vwap_val)
        short_ok = price <= (s1p if not np.isnan(s1p) else vwap_val)
        return long_ok, short_ok

    def _momentum(self, c: np.ndarray, bull: bool)->bool:
        _,_,hist = macd(c, self.macd_fast, self.macd_slow, self.macd_signal)
        r = rsi(c, self.rsi_period)
        if bull:
            macd_ok = (hist[-2] < 0 <= hist[-1]) or (hist[-1] > hist[-2] and hist[-1] >= 0)
            rsi_ok = (r[-1] >= self.rsi_mid) and (np.nanmin(r[-3:]) >= self.rsi_low)
        else:
            macd_ok = (hist[-2] > 0 >= hist[-1]) or (hist[-1] < hist[-2] and hist[-1] <= 0)
            rsi_ok = ( r[-1] <= self.rsi_mid ) or ( (r[-2] >= self.rsi_high) and (r[-1] <= self.rsi_mid) )
        return bool(macd_ok and rsi_ok)

    def _candle_and_volume(self, o,h,l,c,v, bull: bool)->bool:
        o1,h1,l1,c1 = o[-2],h[-2],l[-2],c[-2]
        o2,h2,l2,c2 = o[-1],h[-1],l[-1],c[-1]
        if bull:
            trig = (c1<o1 and c2>o2 and o2<=c1 and c2>=o1) or ((h2-max(c2,o2))<=0.25*(h2-l2) and (min(c2,o2)-l2)>=0.6*(h2-l2)) or (abs(c2-o2)/(h2-l2)>=0.75 and c2>o2)
        else:
            trig = (c1>o1 and c2<o2 and o2>=c1 and c2<=o1) or ((min(c2,o2)-l2)<=0.25*(h2-l2) and (h2-max(c2,o2))>=0.6*(h2-l2)) or (abs(c2-o2)/(h2-l2)>=0.75 and c2<o2)
        N = self.vol_sma_period if len(v)>=self.vol_sma_period else len(v)
        sma = np.nanmean(v[-N:]) if N>0 else np.nanmean(v)
        vol_ok = v[-1] > self.vol_spike_mult * sma
        return bool(trig and vol_ok)

    def _structure(self, h: np.ndarray, l: np.ndarray, c: np.ndarray, bull: bool)->bool:
        res, sup = local_level_breakout(h, l, lookback=10)
        if bull and not np.isnan(res):
            broke = c[-2] > res
            retest = l[-1] <= res * 1.001
            confirm = c[-1] > h[-2]
            return bool(broke and retest and confirm)
        if (not bull) and not np.isnan(sup):
            broke = c[-2] < sup
            retest = h[-1] >= sup * 0.999
            confirm = c[-1] < l[-2]
            return bool(broke and retest and confirm)
        return False

    def evaluate(self, sym: str)->str|None:
        t,o,h,l,c,v = self.m5[sym].arrays()
        if len(c) < 60: return None
        bull, bear = self._bias(sym, c[-1])
        if not (bull or bear):
            return None
        long_ok, short_ok = self._location_vwap(sym, c[-1])
        if bull and not long_ok: return None
        if bear and not short_ok: return None
        cond1 = True
        cond2 = True
        cond3 = self._momentum(c, bull) if (bull or bear) else False
        cond4 = self._candle_and_volume(o,h,l,c,v, bull if bull else False) if (bull or bear) else False
        cond5 = self._structure(h,l,c, bull) if (bull or bear) else False
        count = sum([cond1, cond2, cond3, cond4, cond5])
        if count < self.min_count:
            return None
        key = f"{sym}:{'LONG' if bull else 'SHORT'}"
        now = datetime.now(timezone.utc)
        last = self.last_sent.get(key)
        if last and (now - last) < self.cooldown:
            return None
        atr = atr_rma(h,l,c,14)
        if bull:
            entry = h[-1] * 1.0001
            sl = min(l[-5:]) - self.atr_sl_mult * atr[-1]
            side = 1; direction = "LONG"
        else:
            entry = l[-1] * 0.9999
            sl = max(h[-5:]) + self.atr_sl_mult * atr[-1]
            side = -1; direction = "SHORT"
        R = abs(entry - sl)
        tp1 = entry + side*R
        tp2 = entry + side*2*R
        entry = self._round(sym, entry); sl = self._round(sym, sl); tp1 = self._round(sym, tp1); tp2 = self._round(sym, tp2)
        reasons = []
        if cond3: reasons.append(f"MACD hist + RSI (zones {self.rsi_low}/{self.rsi_mid}/{self.rsi_high})")
        if cond4: reasons.append("Trigger candle + Volume")
        if cond5: reasons.append("Retest & breakout")
        msg = (f"🟢 {self.min_count}/5 | {sym} 5m — {direction}\n"
               f"Вход: {entry}\nSL: {sl}\nTP1: {tp1} | TP2: {tp2}\n"
               f"{' + '.join(reasons) if reasons else 'VWAP/EMA confluence'}")
        self.last_sent[key] = now
        return msg

    def status_snapshot(self, symbols: List[str], tz_name: str)->str:
        out = [f"Symbols: {symbols}",
               f"TZ: {tz_name}",
               f"Min confirmations: {self.min_count}/5",
               f"RSI zones: {self.rsi_low}/{self.rsi_mid}/{self.rsi_high}",
               f"Cooldown: {self.cooldown}",
               f"EMA(1h): {self.ema_fast_1h}/{self.ema_slow_1h}, EMA200(15m): {self.ema_200_15m}",
               f"MACD: {self.macd_fast},{self.macd_slow},{self.macd_signal} | RSI: {self.rsi_period}",
               f"ATR: {self.atr_period} x {self.atr_sl_mult} | VolSMA: {self.vol_sma_period} x{self.vol_spike_mult}",
               f"Supertrend: {'on' if self.supertrend_enabled else 'off'} ({self.supertrend_period},{self.supertrend_multiplier})"]
        return "Status:\n" + "\n".join(out)
