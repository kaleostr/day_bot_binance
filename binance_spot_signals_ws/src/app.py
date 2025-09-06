
from __future__ import annotations
import asyncio
import argparse
import os
import yaml
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List
from .core.rest import BinanceREST
from .core.ws import build_combined_stream_url, ws_consume
from .core.utils import build_tick_map
from .data.candle import Candle
from .storage.memory import TimeSeriesStorage
from .logic.rules import Thresholds, Context
from .signals.detector import detect_signal
from .signals.state import SignalState
from .signals.formatter import format_signal
from .telegram.sender import TelegramClient, telegram_command_loop

class Config:
    def __init__(self, d: dict):
        self.symbols: List[str] = [s.upper() for s in d.get("symbols", ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"])]
        self.timezone: str = d.get("timezone", "Asia/Seoul")
        self.vwap_session_reset: str = d.get("vwap_session_reset", "00:00")
        self.cooldown_minutes_per_symbol: int = int(d.get("cooldown_minutes_per_symbol", 10))
        self.send_startup_message: bool = bool(d.get("send_startup_message", True))
        self.min_alert_level: str = d.get("min_alert_level", "conservative")
        thr = d.get("thresholds", {})
        self.thresholds = Thresholds(
            near_vwap_sigma=float(thr.get("near_vwap_sigma", 1.0)),
            ema_confluence_pct=float(thr.get("ema_confluence_pct", 0.25)),
            impulse_body_factor=float(thr.get("impulse_body_factor", 1.5)),
            vol_spike_factor=float(thr.get("vol_spike_factor", 1.5)),
        )
        self.ws_url: str = d.get("ws_url", "wss://stream.binance.com:9443/stream")
        self.rest_base: str = d.get("rest_base", "https://api.binance.com")
        self.history_bars: int = int(d.get("history_bars", 300))
        self.log_level: str = d.get("log_level", "INFO")

def setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    os.makedirs("/data/logs", exist_ok=True)
    fh = RotatingFileHandler("/data/logs/app.log", maxBytes=5_000_000, backupCount=2)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

class App:
    def __init__(self, cfg: Config, logger: logging.Logger):
        self.cfg = cfg
        self.logger = logger
        self.rest = BinanceREST(cfg.rest_base)
        self.storage = TimeSeriesStorage(maxlen=2000)
        self.state = SignalState(cfg.cooldown_minutes_per_symbol)
        self.ctx = Context(cfg.timezone)
        token = os.environ.get("TG_TOKEN", "")
        chat_id = os.environ.get("TG_CHAT_ID", "")
        self.tg = TelegramClient(token, chat_id) if token and chat_id else None
        self.tick_map: Dict[str, float] = {}
        self.startup_msg_sent = False

    async def backfill(self) -> None:
        self.logger.info("Backfilling history...")
        tasks = []
        for sym in self.cfg.symbols:
            for itv in ["5m","15m","1h"]:
                tasks.append(asyncio.create_task(self._load_one(sym, itv)))
        await asyncio.gather(*tasks)

    async def _load_one(self, symbol: str, interval: str) -> None:
        kl = await self.rest.klines(symbol, interval, self.cfg.history_bars)
        for c in kl:
            self.storage.append(symbol, interval, c)
        self.logger.info(f"Loaded {symbol} {interval}: {len(kl)} bars")

    async def load_exchange_info(self) -> None:
        info = await self.rest.exchange_info(self.cfg.symbols)
        self.tick_map = build_tick_map(info)
        self.logger.info("Exchange info loaded (tick sizes).")

    async def on_kline_closed(self, symbol: str, interval: str, k: dict) -> None:
        c = Candle(
            open_time=k["t"], open=float(k["o"]), high=float(k["h"]), low=float(k["l"]),
            close=float(k["c"]), volume=float(k["v"]), close_time=k["T"], is_closed=True
        )
        self.storage.append(symbol, interval, c)
        if interval != "5m":
            return
        m5 = self.storage.get_series(symbol, "5m")
        m15 = self.storage.get_series(symbol, "15m")
        h1 = self.storage.get_series(symbol, "1h")
        if len(m5) < 30 or len(m15) < 200 or len(h1) < 60:
            return
        res = detect_signal(
            symbol, self.tick_map.get(symbol, 0.00000001), list(h1), list(m15), list(m5),
            self.cfg.thresholds, self.ctx, self.cfg.min_alert_level
        )
        if not res.should_send:
            return
        key = (symbol, res.side)
        bar_dt = c.close_dt
        if not self.state.can_send(key, bar_dt):
            return
        self.state.mark_sent(key, bar_dt)
        if self.tg:
            text = format_signal(res.level_emoji, res.level_name, symbol, "5m", res.side, res.entry, res.sl, res.tp1, res.tp2, res.reason)
            await self.tg.send_message(text)
            self.logger.info(f"Signal sent: {text.replace('\n',' | ')}")
        else:
            self.logger.info("TG not configured, skipping send.")

    def get_status_text(self) -> str:
        return f"Symbols: {', '.join(self.cfg.symbols)} | Min level: {self.cfg.min_alert_level} | TZ: {self.cfg.timezone}"

    async def startup_message_once(self) -> None:
        if self.cfg.send_startup_message and self.tg and not self.startup_msg_sent:
            await self.tg.send_message("✅ Binance Spot Signals bot started.")
            self.startup_msg_sent = True

    async def run(self) -> None:
        await self.load_exchange_info()
        await self.backfill()
        await self.startup_message_once()
        url = build_combined_stream_url(self.cfg.ws_url, self.cfg.symbols)
        self.logger.info(f"WS URL: {url}")
        tg_task = asyncio.create_task(telegram_command_loop(self.tg, self.get_status_text)) if self.tg else None
        try:
            await ws_consume(url, self.on_kline_closed)
        finally:
            if tg_task:
                tg_task.cancel()

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    with open(args.config, "r") as f:
        cfg = Config(yaml.safe_load(f))
    logger = setup_logger(cfg.log_level)
    app = App(cfg, logger)
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())
