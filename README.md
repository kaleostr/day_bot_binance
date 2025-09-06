# Vyacheslav — Home Assistant Add-ons (v1.7.3)

Этот репозиторий содержит аддон **Binance Spot Signals (WebSocket)** v1.7.3.
Исправления:
- Убран `bashio` из `run.sh` (теперь обычный bash) — бот корректно стартует.
- `schema.symbol_overrides` → строка `"str?"`, в `options` — `symbol_overrides: ""`.
- LONG-only, «один сигнал на бар», Asia/Seoul. Подтверждения 3 из 5 с обязательными группами.

## Как использовать
1) Залейте содержимое этого архива в **public** GitHub-репозиторий.
2) В Home Assistant: **Add-on Store → ⋮ → Repositories → Add** — вставьте URL вашего репозитория → **Reload**.
3) Откройте карточку вашего репозитория внизу магазина и установите аддон.
