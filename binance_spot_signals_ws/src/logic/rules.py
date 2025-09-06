
from __future__ import annotations
from typing import Dict, List, Tuple
from ..data.candle import Candle
from ..indicators.ema import ema
from ..indicators.macd import macd
from ..indicators.rsi import rsi
from ..indicators.atr import atr_rma
from ..indicators.vwap_session import VWAPSession
from .patterns import bullish_engulfing, bearish_engulfing, bullish_pinbar, bearish_pinbar, impulse_body, breakout_high, breakout_low

class Thresholds:
    def __init__(self, near_vwap_sigma: float = 1.0, ema_confluence_pct: float = 0.25, impulse_body_factor: float = 1.5, vol_spike_factor: float = 1.5):
        self.near_vwap_sigma = near_vwap_sigma
        self.ema_confluence_pct = ema_confluence_pct
        self.impulse_body_factor = impulse_body_factor
        self.vol_spike_factor = vol_spike_factor

class Context:
    def __init__(self, tz_name: str = "Asia/Seoul"):
        self.vwap_sessions: Dict[str, VWAPSession] = {}
        self.tz_name = tz_name

    def vwap_sess(self, symbol: str) -> VWAPSession:
        if symbol not in self.vwap_sessions:
            self.vwap_sessions[symbol] = VWAPSession(self.tz_name)
        return self.vwap_sessions[symbol]

def compute_bias_1h(symbol: str, h1: List[Candle], m15: List[Candle]) -> Tuple[str, Dict[str, float]]:
    if len(h1) < 60 or len(m15) < 200:
        return "none", {}
    closes_h1 = [c.close for c in h1]
    ema20_h1 = ema(closes_h1, 20)
    ema50_h1 = ema(closes_h1, 50)
    trend = "bull" if ema20_h1[-1] > ema50_h1[-1] else ("bear" if ema20_h1[-1] < ema50_h1[-1] else "none")
    ema200_15 = ema([c.close for c in m15], 200)
    price_15 = m15[-1].close
    above_200 = price_15 > ema200_15[-1]
    below_200 = price_15 < ema200_15[-1]
    if trend == "bull" and above_200:
        return "bull", {"ema20_h1": ema20_h1[-1], "ema50_h1": ema50_h1[-1], "ema200_15": ema200_15[-1]}
    if trend == "bear" and below_200:
        return "bear", {"ema20_h1": ema20_h1[-1], "ema50_h1": ema50_h1[-1], "ema200_15": ema200_15[-1]}
    return "none", {}

def compute_setup_15m(symbol: str, m15: List[Candle], ctx: Context, thr: Thresholds) -> Dict[str, float | bool]:
    if len(m15) < 200:
        return {"near_vwap": False, "ema_confluence": False}
    sess = ctx.vwap_sess(symbol)
    last = m15[-1]
    vwap, sigma = sess.update(last.close, last.volume, last.close_dt)
    near_vwap = abs(last.close - vwap) <= thr.near_vwap_sigma * sigma if sigma > 0 else True
    ema20 = ema([c.close for c in m15], 20)[-1]
    ema50 = ema([c.close for c in m15], 50)[-1]
    ema_conf = (abs(last.close - ema20)/ema20*100 <= thr.ema_confluence_pct) or (abs(last.close - ema50)/ema50*100 <= thr.ema_confluence_pct)
    return {"near_vwap": near_vwap, "ema_confluence": ema_conf, "vwap": vwap, "sigma": sigma, "ema20_15": ema20, "ema50_15": ema50}

def momentum_5m(m5: List[Candle]) -> Dict[str, float | bool]:
    closes = [c.close for c in m5]
    macd_line, sig, hist = macd(closes, 12, 26, 9)
    rsi14 = rsi(closes, 14)
    return {
        "macd_hist": hist[-1] if hist else 0.0,
        "macd_hist_prev": hist[-2] if len(hist) > 1 else 0.0,
        "rsi": rsi14[-1] if rsi14 else 50.0,
        "rsi_prev": rsi14[-2] if len(rsi14) > 1 else 50.0,
    }

def candle_trigger_5m(m5: List[Candle], thr: Thresholds) -> Dict[str, bool | float]:
    if len(m5) < 25: 
        return {"vol_spike": False, "pattern_bull": False, "pattern_bear": False, "impulse": False, "avg_body": 0.0}
    prev = m5[-2]
    curr = m5[-1]
    bodies = [abs(c.close - c.open) for c in m5[-20:]]
    avg_body = sum(bodies)/len(bodies)
    vol_sma20 = sum([c.volume for c in m5[-20:]])/20.0
    vol_spike = curr.volume > thr.vol_spike_factor * vol_sma20
    pat_bull = bullish_engulfing(prev, curr) or bullish_pinbar(curr) or (abs(curr.close - curr.open) >= avg_body * thr.impulse_body_factor)
    pat_bear = bearish_engulfing(prev, curr) or bearish_pinbar(curr) or (abs(curr.close - curr.open) >= avg_body * thr.impulse_body_factor)
    return {"vol_spike": vol_spike, "pattern_bull": pat_bull, "pattern_bear": pat_bear, "impulse": abs(curr.close - curr.open) >= avg_body * thr.impulse_body_factor, "avg_body": avg_body}

def structure_5m(m5: List[Candle], lookback: int = 10) -> Dict[str, bool]:
    highs = [c.high for c in m5]
    lows = [c.low for c in m5]
    def breakout_high(highs: List[float], lookback: int) -> bool:
        if len(highs) < lookback+1: return False
        prev_max = max(highs[-(lookback+1):-1])
        return highs[-1] > prev_max
    def breakout_low(lows: List[float], lookback: int) -> bool:
        if len(lows) < lookback+1: return False
        prev_min = min(lows[-(lookback+1):-1])
        return lows[-1] < prev_min
    return {"breakout_high": breakout_high(highs, lookback), "breakout_low": breakout_low(lows, lookback)}

def pick_level_name(cnt_all_five: int, cnt_3_5: int, has_bias_and_setup: bool, min_level: str) -> tuple[str, str]:
    if cnt_all_five >= 4:
        return "🟢", "Консервативный"
    if cnt_3_5 >= 3 and has_bias_and_setup:
        return "🟡", "Базовый"
    if cnt_3_5 >= 2 and has_bias_and_setup:
        return "🟠", "Агрессивный"
    return "", ""
