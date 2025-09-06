# Vyacheslav — Home Assistant Add-ons

Этот репозиторий содержит аддоны для Home Assistant.

## Подключение в Home Assistant
1. Settings → Add-ons → **Add-on Store** → меню (⋮) → **Repositories** → добавьте URL этого репозитория GitHub.
2. Найдите в списке **Binance Spot Signals (WebSocket)** → Install.
3. Во вкладке **Configuration**:
   - `preset`: balanced / conservative / active
   - `long_only: true`
   - `timezone: Asia/Seoul`, `vwap_session_reset: "00:00"`
   - `cooldown_minutes_per_symbol: 10`
   - Заполните `tg_token`, `tg_chat_id`.
4. Нажмите **Save** → **Start**.

> Опционально: добавьте CI/CD в `.github/workflows/build.yml`, чтобы собирать и публиковать Docker-образы в GHCR, и укажите в `config.yaml` строку `image:`.
