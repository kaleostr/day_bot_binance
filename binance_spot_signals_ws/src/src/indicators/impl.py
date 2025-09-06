from __future__ import annotations
import numpy as np

def ema(arr: np.ndarray, period: int) -> np.ndarray:
    alpha = 2/(period+1)
    out = np.empty_like(arr)
    out[:] = np.nan
    if len(arr)==0:
        return out
    # seed
    s = np.nanmean(arr[:period])
    out[period-1] = s
    for i in range(period, len(arr)):
        s = alpha*arr[i] + (1-alpha)*s
        out[i] = s
    return out

def rsi(close: np.ndarray, period: int=14) -> np.ndarray:
    diff = np.diff(close, prepend=close[0])
    gain = np.where(diff>0, diff, 0.0)
    loss = np.where(diff<0, -diff, 0.0)
    alpha = 1/period
    # RMA
    avg_gain = np.empty_like(close); avg_gain[:] = np.nan
    avg_loss = np.empty_like(close); avg_loss[:] = np.nan
    g = np.nanmean(gain[1:period+1]); l = np.nanmean(loss[1:period+1])
    avg_gain[period] = g; avg_loss[period] = l
    for i in range(period+1, len(close)):
        g = (g*(period-1) + gain[i])/period
        l = (l*(period-1) + loss[i])/period
        avg_gain[i] = g; avg_loss[i] = l
    rs = avg_gain/np.where(avg_loss==0, np.nan, avg_loss)
    rsi = 100 - (100/(1+rs))
    return rsi

def macd(close: np.ndarray, fast=12, slow=26, signal=9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def atr_rma(high: np.ndarray, low: np.ndarray, close: np.ndarray, period=14) -> np.ndarray:
    tr = np.maximum.reduce([high-low, np.abs(high - np.roll(close,1)), np.abs(low - np.roll(close,1))])
    tr[0] = high[0]-low[0]
    out = np.empty_like(tr); out[:] = np.nan
    v = np.nanmean(tr[1:period+1])
    out[period] = v
    for i in range(period+1, len(tr)):
        v = (v*(period-1) + tr[i])/period
        out[i] = v
    return out

class VWAPSession:
    def __init__(self):
        self.reset()

    def reset(self):
        self.sum_pv = 0.0
        self.sum_v = 0.0
        self.values = []  # store typical price for sigma bands calc

    def update(self, price: float, volume: float):
        self.sum_pv += price*volume
        self.sum_v += volume
        self.values.append(price)

    def vwap(self):
        return self.sum_pv/self.sum_v if self.sum_v>0 else np.nan

    def sigma(self):
        arr = np.array(self.values, dtype=float)
        if len(arr) < 2: return (np.nan, np.nan)
        m = np.nanmean(arr); s = np.nanstd(arr)
        return (m+s, m+2*s, m-s, m-2*s)
