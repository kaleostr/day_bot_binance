
from __future__ import annotations

def format_signal(level_emoji: str, level_name: str, symbol: str, tf: str, side: str,
                  entry: float, sl: float, tp1: float, tp2: float, reason: str) -> str:
    title = f"{level_emoji} {level_name} | {symbol} {tf} — {side}"
    body = f"Вход: {entry:.6f}\nSL: {sl:.6f}\nTP1: {tp1:.6f} | TP2: {tp2:.6f}\n{reason}"
    return f"{title}\n{body}"
