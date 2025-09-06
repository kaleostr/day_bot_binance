# Binance Spot Signals (WebSocket) — HA Add-on

Версия 1.5.0: 
- Порог подтверждений теперь **строго N-из-5** (1..5): любые N условий из пяти дают сигнал.
- Убран `min_alert_level` (строковый). Используй только `min_alert_level_n`.
- Пять условий: Trend, Location(VWAP/σ), Momentum(MACD+RSI zones), Trigger candle+Volume, Structure(retest/breakout).
