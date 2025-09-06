# Vyacheslav — Home Assistant Add-ons (v1.6.2)

Репозиторий аддонов Home Assistant. Включает:
- **Binance Spot Signals (WebSocket)** v1.6.2 — интрадей-бот (LONG-only), логика 3 из 5 с обязательными группами, VWAP Session, жёсткие блок-фильтры, ATR-стопы/тейки.

## Установка
1) Опубликуйте этот репозиторий на GitHub (public).
2) В Home Assistant → **Add-on Store** → меню ⋮ → **Repositories** → добавьте URL своего репозитория → **Reload**.
3) Откройте карточку репозитория внизу и установите аддон.

## Примечания
- В настройках аддона укажите `tg_token` и `tg_chat_id`.
- `symbol_overrides` — строка; можно вставлять YAML-карту для пер-символьных оверрайдов.
