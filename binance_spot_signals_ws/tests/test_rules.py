
from datetime import datetime, timezone
from src.data.candle import Candle
from src.logic.rules import Thresholds, Context
from src.signals.detector import detect_signal

def make_candle(ts, o,h,l,c,v):
    return Candle(open_time=ts, open=o, high=h, low=l, close=c, volume=v, close_time=ts+60_000*5, is_closed=True)

def test_rule_runs():
    now = int(datetime.now(tz=timezone.utc).timestamp()*1000)
    m5 = [make_candle(now-60_000*5*(50-i), 100+i*0.2, 100+i*0.25, 100+i*0.15, 100+i*0.22, 100+i*2) for i in range(50)]
    m15 = [make_candle(now-60_000*15*(220-i), 100+i*0.4, 100+i*0.5, 100+i*0.3, 100+i*0.45, 100+i*5) for i in range(220)]
    h1 = [make_candle(now-60_000*60*(80-i),  90+i*0.6,  90+i*0.7,  90+i*0.5,  90+i*0.65, 100+i*10) for i in range(80)]
    thr = Thresholds()
    ctx = Context("Asia/Seoul")
    res = detect_signal("TESTUSDT", 0.01, h1, m15, m5, thr, ctx, "conservative")
    assert res is not None
