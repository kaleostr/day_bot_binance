# Binance Spot Signals (WebSocket) — Home Assistant Add-on

- Uses official HA add-on style: `config.yaml` manifest, `ARG BUILD_FROM` in `Dockerfile`, run script with `/usr/bin/with-contenv bashio` (per HA developer docs).
- Async Python bot: REST backfill + WebSocket (1h/15m/5m), numpy indicators (EMA/MACD/RSI/ATR/VWAP).
- Telegram alerts with dedupe/cooldown.

## Configure tokens
Put a file `.env` with your Telegram token & chat in **/addon_configs/binance_spot_signals_ws/.env** (or `/data/.env`):

```
TG_TOKEN=123456:ABC-DEF
TG_CHAT_ID=12345678
```

Options are available in the add-on UI and rendered to `/data/config.yaml` on start.
