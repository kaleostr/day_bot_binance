
from __future__ import annotations
from typing import List
from ..data.candle import Candle
from ..core.utils import round_to_tick
from ..logic.rules import Thresholds, Context, compute_bias_1h, compute_setup_15m, momentum_5m, candle_trigger_5m, structure_5m, pick_level_name

class SignalResult:
    def __init__(self, should_send: bool, side: str = "", level_emoji: str = "", level_name: str = "", entry: float = 0.0, sl: float = 0.0, tp1: float = 0.0, tp2: float = 0.0, reason: str = ""):
        self.should_send = should_send
        self.side = side
        self.level_emoji = level_emoji
        self.level_name = level_name
        self.entry = entry
        self.sl = sl
        self.tp1 = tp1
        self.tp2 = tp2
        self.reason = reason

def detect_signal(symbol: str, tick: float, h1: List[Candle], m15: List[Candle], m5: List[Candle], thr: Thresholds, ctx: Context, min_level: str) -> SignalResult:
    if len(m5) < 30 or len(m15) < 200 or len(h1) < 60:
        return SignalResult(False)
    bias, meta = compute_bias_1h(symbol, h1, m15)
    setup = compute_setup_15m(symbol, m15, ctx, thr)
    mom = momentum_5m(m5)
    trig = candle_trigger_5m(m5, thr)
    struct = structure_5m(m5, 10)
    last = m5[-1]

    rule1_bull = bias == "bull"
    rule1_bear = bias == "bear"
    rule2_loc = bool(setup.get("near_vwap") or setup.get("ema_confluence"))

    mom_bull = (mom["macd_hist_prev"] <= 0 and mom["macd_hist"] > 0) and (mom["rsi"] >= 50 or (mom["rsi_prev"] < 45 and mom["rsi"] >= 45 and mom["rsi"] > mom["rsi_prev"]))
    mom_bear = (mom["macd_hist_prev"] >= 0 and mom["macd_hist"] < 0) and (mom["rsi"] <= 50 or (mom["rsi_prev"] > 55 and mom["rsi"] <= 55 and mom["rsi"] < mom["rsi_prev"]))

    trig_bull = bool(trig["pattern_bull"] and trig["vol_spike"])
    trig_bear = bool(trig["pattern_bear"] and trig["vol_spike"])

    struct_bull = bool(struct["breakout_high"])
    struct_bear = bool(struct["breakout_low"])

    cnt_3_5_bull = sum([mom_bull, trig_bull, struct_bull])
    cnt_3_5_bear = sum([mom_bear, trig_bear, struct_bear])

    cnt_all_bull = sum([rule1_bull, rule2_loc, mom_bull, trig_bull, struct_bull])
    cnt_all_bear = sum([rule1_bear, rule2_loc, mom_bear, trig_bear, struct_bear])

    has_bias_and_setup_bull = rule1_bull and rule2_loc
    has_bias_and_setup_bear = rule1_bear and rule2_loc

    lvl_emoji_bull, lvl_name_bull = pick_level_name(cnt_all_bull, cnt_3_5_bull, has_bias_and_setup_bull, min_level)
    lvl_emoji_bear, lvl_name_bear = pick_level_name(cnt_all_bear, cnt_3_5_bear, has_bias_and_setup_bear, min_level)

    def allow(level_name: str) -> bool:
        order = {"aggressive": 0, "base": 1, "conservative": 2}
        inv = {"Агрессивный": "aggressive", "Базовый": "base", "Консервативный": "conservative"}
        min_idx = order.get(min_level, 2)
        cur = order.get(inv.get(level_name, "conservative"), 2)
        return cur >= min_idx

    if lvl_name_bull and allow(lvl_name_bull):
        entry = round_to_tick(last.high * 1.0001, tick)
        swing_low = min(c.low for c in m5[-10:])
        vwap = float(setup.get("vwap", last.close))
        atr = _avg_true_range(m5)
        sl_candidate = min(swing_low, vwap)
        sl = round_to_tick(min(entry - 1.3 * atr, sl_candidate), tick)
        r = entry - sl
        tp1 = round_to_tick(entry + r * 1.0, tick)
        tp2 = round_to_tick(entry + r * 2.0, tick)
        reason = _build_reason(True, rule2_loc, mom_bull, trig_bull, struct_bull)
        return SignalResult(True, "LONG", lvl_emoji_bull, lvl_name_bull, entry, sl, tp1, tp2, reason)

    if lvl_name_bear and allow(lvl_name_bear):
        entry = round_to_tick(last.low * 0.9999, tick)
        swing_high = max(c.high for c in m5[-10:])
        vwap = float(setup.get("vwap", last.close))
        atr = _avg_true_range(m5)
        sl_candidate = max(swing_high, vwap)
        sl = round_to_tick(max(entry + 1.3 * atr, sl_candidate), tick)
        r = sl - entry
        tp1 = round_to_tick(entry - r * 1.0, tick)
        tp2 = round_to_tick(entry - r * 2.0, tick)
        reason = _build_reason(False, rule2_loc, mom_bear, trig_bear, struct_bear)
        return SignalResult(True, "SHORT", lvl_emoji_bear, lvl_name_bear, entry, sl, tp1, tp2, reason)

    return SignalResult(False)

def _avg_true_range(m5: List[Candle]) -> float:
    if len(m5) < 14:
        return max((c.high - c.low) for c in m5[-5:])
    trs = []
    for i in range(len(m5)):
        if i == 0:
            trs.append(m5[i].high - m5[i].low)
        else:
            tr = max(m5[i].high - m5[i-1].close, m5[i-1].close - m5[i].low, m5[i].high - m5[i].low)
            trs.append(tr)
    period = 14
    avg = trs[0]
    for i, v in enumerate(trs):
        if i == 0:
            avg = v
        else:
            avg = (avg*(period-1)+v)/period
    return avg

def _build_reason(is_long: bool, setup_ok: bool, mom: bool, trig: bool, struct: bool) -> str:
    parts = []
    if setup_ok:
        parts.append("VWAP/EMA retest")
    if mom:
        parts.append("MACD flip + RSI")
    if trig:
        parts.append("Trigger + Volume spike")
    if struct:
        parts.append("Breakout/Retest")
    return " | ".join(parts) or "Setup OK"
