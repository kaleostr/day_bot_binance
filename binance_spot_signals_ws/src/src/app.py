import asyncio, json, math, time, logging
from typing import Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta

import httpx
import websockets
import yaml
import numpy as np
from pydantic import BaseModel

from src.core.exchange import BinanceREST, BinanceWS
from src.logic.engine import SignalEngine
from src.telegram.notify import Telegram

logger = logging.getLogger("app")

class Config(BaseModel):
    symbols: List[str]
    timezone: str = "Asia/Seoul"
    vwap_session_reset: str = "00:00"
    cooldown_minutes_per_symbol: int = 10
    send_startup_message: bool = True
    min_alert_level: str = "conservative"
    ws_url: str = "wss://stream.binance.com:9443/stream"
    rest_base: str = "https://api.binance.com"
    history_bars: int = 300
    log_level: str = "INFO"

async def main(config_path: str):
    with open(config_path, "r") as f:
        cfg = Config(**yaml.safe_load(f))

    logging.basicConfig(level=getattr(logging, cfg.log_level.upper(), logging.INFO),
                        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    tz = ZoneInfo(cfg.timezone)
    rest = BinanceREST(cfg.rest_base)
    tick_size = await rest.get_tick_size_map(cfg.symbols)

    tg = Telegram.from_env()
    engine = SignalEngine(tz=tz,
                          vwap_reset_local=cfg.vwap_session_reset,
                          cooldown_minutes=cfg.cooldown_minutes_per_symbol,
                          min_level=cfg.min_alert_level,
                          tick_size=tick_size,
                          telegram=tg)

    # preload history
    for sym in cfg.symbols:
        h1 = await rest.get_klines(sym, "1h", cfg.history_bars)
        m15 = await rest.get_klines(sym, "15m", cfg.history_bars)
        m5 = await rest.get_klines(sym, "5m", cfg.history_bars)
        engine.warmup(sym, h1, m15, m5)

    if cfg.send_startup_message and tg.available:
        await tg.send(f"✅ Bot started. TZ={cfg.timezone}, symbols={cfg.symbols}")

    # start WS
    ws = BinanceWS(cfg.ws_url, cfg.symbols)
    async for event in ws.stream():
        if event["type"] == "kline_close":
            sym = event["symbol"]
            interval = event["interval"]
            k = event["kline"]
            engine.on_close(sym, interval, k)

            if interval == "5m":
                msg = engine.evaluate(sym)
                if msg:
                    await tg.send(msg)


if __name__ == "__main__":
    import argparse, asyncio
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    asyncio.run(main(args.config))
