
# Binance Spot Signals (WebSocket) — v1.6.2

- LONG-only, Asia/Seoul, «один сигнал на бар»
- Подтверждения 3 из 5 с обязательными группами: (trend≥1) ∧ (momentum≥1) ∧ (liquidity≥1) ∧ (count_true≥3)
- VWAP Session (сброс 00:00 KST) с полосами ±1σ/±2σ
- Жёсткие блок-фильтры (RSI1h<block, >+2σ без отката, верхняя тень/ATR>0.6)
- Риск: SL=ATR×1.3; TP1/2/3 = 0.5/1.0/1.5 R; трейлинг ATR×0.8 или VWAP (ближайший)
- Команды Telegram: /ping, /status

**symbol_overrides** — вставляйте YAML-карту в UI как строку, например:
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
