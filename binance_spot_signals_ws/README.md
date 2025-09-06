# Binance Spot Signals (WebSocket) — Home Assistant Add-on

- Async бот: REST backfill (300 баров), WebSocket комбинированный поток (1h/15m/5m), EMA/MACD/RSI/ATR, VWAP (сброс 00:00 KST), анти-дубль и cooldown, отправка сигналов в Telegram.
- Полностью совместим с Raspberry Pi 5 (aarch64).
- Опции аддона задаются в UI, при старте читаются из `/data/options.json` (стандарт Home Assistant).
- Секреты (TG токен/чат) хранятся в `/addon_configs/binance_spot_signals_ws/.env`.

## Установка
1. Залей весь репозиторий на GitHub (Public). В корне: `repository.json` и папка `binance_spot_signals_ws/`.
2. В Home Assistant → Add-on Store → ⋮ → Repositories → Add → URL твоего репо → Add → Close → Check for updates.
3. Установи “Binance Spot Signals (WebSocket)”, включи Autostart и Watchdog.
4. Создай файл `/addon_configs/binance_spot_signals_ws/.env`:
```
TG_TOKEN=...    # токен твоего бота
TG_CHAT_ID=...  # id твоего чата
```
5. Запусти аддон. В логе увидишь Backfilling и WS connected. В Telegram: `/ping` (pong), `/status` (сводка).

