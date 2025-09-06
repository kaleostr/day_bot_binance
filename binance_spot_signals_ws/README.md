# Binance Spot Signals (WebSocket) — HA Add-on

**Версия 1.7.1** (LONG-only, KST, «один сигнал на бар», пресеты в UI).

### Как включить GHCR-образы
1. В `config.yaml` раскомментируйте строку `image:` и подставьте ваш `OWNER`:
   ```yaml
   image: "ghcr.io/OWNER/{arch}-addon-binance_spot_signals_ws"
   ```
2. Дайте workflow-токену права *write* (Settings → Actions → General).
3. После первой сборки сделайте GHCR-пакет **Public**.
4. В HA: Add-on Store → ⋮ → **Check for updates** → Rebuild/Update.

### Команды Telegram
- `/ping` — проверка
- `/status` — сводка текущих настроек и статуса
