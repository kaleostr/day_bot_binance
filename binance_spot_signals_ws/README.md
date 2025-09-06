# Binance Spot Signals (WebSocket) — HA Add-on

**Версия 1.7.1** (LONG-only, KST, «один сигнал на бар», пресеты в UI).

## Конфиг по умолчанию
- Пресет **balanced**: `confirmations_min=3`, `rsi1h_block=50`, `volume_spike_mult=1.5`, `cooldown=10m`
- LONG-only: `true`
- Внутренняя логика: агрегатор **3 из 5** с обязательными группами (тренд ∧ моментум ∧ ликвидность), VWAP-сессия, блок-фильтры, трейлинг.

## Команды
- `/ping` — проверка
- `/status` — сводка статуса

## Иконки
`icon.png` и `logo.png` лежат в папке аддона.
