
# Binance Spot WebSocket Signals Bot — Home Assistant Add-on

**Назначение**: Реальный asyncio‑бот для спота Binance. Получает свечи через **Binance WebSocket Streams**
(1h/15m/5m), считает индикаторы (EMA 20/50/200, VWAP c σ‑полосами, MACD 12‑26‑9, RSI 14, ATR(14) RMA,
объёмные спайки) и отправляет сигналы LONG/SHORT в Telegram **только на закрытии 5m свечи**.
Сигналы де‑дублируются, есть **COOLDOWN**, авто‑reconnect WS, логирование с ротацией.

Работает как **Home Assistant OS Add‑on** (Raspberry Pi 5 поддержан), а также как обычный Docker‑контейнер.

---

## ⚙️ Параметры по умолчанию

- `SYMBOLS`: `["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]`
- `TIMEZONE`: `Asia/Seoul`
- `VWAP_SESSION_RESET`: `00:00` (KST)
- `COOLDOWN_MINUTES_PER_SYMBOL`: `10`
- `SEND_STARTUP_MESSAGE`: `true`
- `MIN_ALERT_LEVEL`: `conservative` (`aggressive` | `base` | `conservative`)

Секреты в `.env`:
- `TG_TOKEN`: токен бота Telegram
- `TG_CHAT_ID`: ID чата для отправки сообщений

**Команды Telegram**: `/ping`, `/status`

---

## 🧱 Установка как Home Assistant Add-on

1. Скопируйте весь репозиторий в локальный репозиторий аддонов Home Assistant (или
   загрузите zip и распакуйте в отдельную папку).
2. В папке аддона будут файлы:
   - `Dockerfile`
   - `config.json` — манифест аддона
   - `run.sh` — стартовый скрипт
   - `requirements.txt`, каталог `src/`
3. В **/data** аддона создайте/отредактируйте:
   - `/data/.env` — токен и чат:
     ```env
     TG_TOKEN=7929566269:AAGB5nz6hMwHPE5AKqY5orAyNeZXy_DzBkI
     TG_CHAT_ID=311797898
     ```
   - `/data/config.yaml` — основные настройки (см. пример ниже).
4. Перезапустите аддон.

### Пример `/data/config.yaml`

```yaml
symbols: ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]
timezone: "Asia/Seoul"
vwap_session_reset: "00:00"   # время старта дневной сессии KST
cooldown_minutes_per_symbol: 10
send_startup_message: true
min_alert_level: "conservative"  # aggressive|base|conservative
thresholds:
  near_vwap_sigma: 1.0     # близость к VWAP: внутри ±1σ
  ema_confluence_pct: 0.25 # % до EMA20/50 для confluence
  impulse_body_factor: 1.5 # импульс: тело > 1.5× средний body(20)
  vol_spike_factor: 1.5    # объёмный спайк: > 1.5× SMA20(volume)
ws_url: "wss://stream.binance.com:9443/stream"
rest_base: "https://api.binance.com"
history_bars: 300
log_level: "INFO"
```

---

## 🐳 Запуск вне Home Assistant (Docker)

```bash
docker build -t binance-signals:latest .
docker run --name binance-bot --restart=unless-stopped   -v $(pwd)/data:/data   -e TZ=Asia/Seoul   binance-signals:latest
```

Где `./data` содержит `.env` и `config.yaml` как выше.

---

## 🧪 Тесты и CI

- Юнит‑тесты (`pytest`) на индикаторы и правило 4/5.
- Линтеры: `ruff`, форматирование `black`, типы `mypy`.
- GitHub Actions workflow: тесты + сборка Docker‑образа (при наличии секретов).

---

## 📨 Формат сообщения

```
🟢 Консервативный | SOLUSDT 5m — LONG
Вход: 204.0800
SL: 203.6688
TP1: 204.4912 | TP2: 204.9024
VWAP/EMA retest
```

**Анти‑спам**: один сигнал на один и тот же сетап/направление/символ до смены состояния, плюс
`COOLDOWN_MINUTES_PER_SYMBOL`.

---

## 📜 Логи старта (пример)

```
[INFO] Loading config...
[INFO] Backfilling history: BTCUSDT (5m/15m/1h) — 300 bars
[INFO] WebSocket connected (combined streams).
[INFO] Telegram startup message sent once.
```

---

## 🔒 Примечания безопасности
- Храните `.env` отдельно, не коммитьте его в публичный репозиторий.
- Токен Telegram не публикуйте.
