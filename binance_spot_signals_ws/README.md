
# Binance Spot Signals (WebSocket) — v1.7.3

- LONG-only, «один сигнал на бар», Asia/Seoul
- Подтверждения 3 из 5 с обязательными группами (bias/momentum/liquidity)
- VWAP Session (00:00 KST) с полосами ±1σ/±2σ
- Жёсткие блок-фильтры, трейлинг по ATR/VWAP
- Команды: /ping, /status

**ВАЖНО:** `symbol_overrides` — строка. Вставляйте YAML-карту, например:
```yaml
BTCUSDT:
  confirmations_min: 4
XRPUSDT:
  confirmations_min: 4
  volume_spike_mult: 1.7
  atr_sl_mult: 1.6
SOLUSDT:
  require_macd_and_rsi: true
  atr_sl_mult: 1.4
```
