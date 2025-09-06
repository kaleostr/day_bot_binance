
from __future__ import annotations
from typing import List
from ..data.candle import Candle

def bullish_engulfing(prev: Candle, curr: Candle) -> bool:
    return (prev.close < prev.open) and (curr.close > curr.open) and (curr.close >= prev.open) and (curr.open <= prev.close)

def bearish_engulfing(prev: Candle, curr: Candle) -> bool:
    return (prev.close > prev.open) and (curr.close < curr.open) and (curr.close <= prev.open) and (curr.open >= prev.close)

def bullish_pinbar(c: Candle) -> bool:
    body = abs(c.close - c.open)
    lower = min(c.open, c.close) - c.low
    upper = c.high - max(c.open, c.close)
    return lower > body * 2 and upper < body

def bearish_pinbar(c: Candle) -> bool:
    body = abs(c.close - c.open)
    upper = c.high - max(c.open, c.close)
    lower = min(c.open, c.close) - c.low
    return upper > body * 2 and lower < body

def impulse_body(body: float, avg_body: float, factor: float = 1.5) -> bool:
    return body >= avg_body * factor

def breakout_high(highs: List[float], lookback: int = 10) -> bool:
    if len(highs) < lookback+1: return False
    prev_max = max(highs[-(lookback+1):-1])
    return highs[-1] > prev_max

def breakout_low(lows: List[float], lookback: int = 10) -> bool:
    if len(lows) < lookback+1: return False
    prev_min = min(lows[-(lookback+1):-1])
    return lows[-1] < prev_min
