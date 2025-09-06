
from src.indicators.ema import ema
from src.indicators.macd import macd
from src.indicators.rsi import rsi
from src.indicators.atr import atr_rma

def test_ema_monotonic():
    data = [i for i in range(1, 51)]
    e = ema(data, 10)
    assert len(e) == len(data)
    assert e[-1] > e[0]

def test_macd_shapes():
    data = [i for i in range(1, 100)]
    m, s, h = macd(data, 12, 26, 9)
    assert len(m) == len(data)
    assert len(s) == len(data)
    assert len(h) == len(data)

def test_rsi_bounds():
    data = [1,2,3,4,5,4,3,2,3,4,5,6,7,8,9,10]
    r = rsi(data, 14)
    assert len(r) == len(data)
    assert all(0 <= x <= 100 for x in r if x == x)

def test_atr_nonnegative():
    import random
    highs, lows, closes = [], [], []
    p = 100.0
    for _ in range(30):
        h = p + random.random()
        l = p - random.random()
        c = l + (h - l) * random.random()
        highs.append(h); lows.append(l); closes.append(c); p = c
    a = atr_rma(highs, lows, closes, 14)
    assert len(a) == len(closes)
    assert all(x >= 0 for x in a)
