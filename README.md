# Binance Spot Signal Bot (Home Assistant Add-on)

**Версия:** 0.1  
**Web UI:** `http://[HOST]:8181`

## Что делает аддон
Сканирует спот‑пары Binance (топ по 24ч `quoteVolume`), тянет свечи 1h/15m/5m, добавляет индикаторы (EMA 20/50/200, MACD 12‑26‑9, RSI 14, VWAP, ATR) и отправляет сигналы в Telegram по правилам подтверждений.

## Установка из GitHub
1. В Home Assistant откройте *Settings → Add-ons → Add-on Store → ⋮ → Repositories* и добавьте URL репозитория, куда вы выложите этот аддон.
2. Найдите **Binance Spot Signal Bot** → *Install* → *Start* → *Open Web UI*.

## Настройка
В *Configuration* укажите:
- `telegram_token`, `telegram_chat_id`
- `symbols_quote` (по умолчанию `USDT`)
- `top_n_by_volume` (например, 120)
- `min_vol_24h_usd` (например, 5000000)
- `use_level1_spread` (учитывать спред при TP)
После запуска бот пришлёт в Telegram сообщение: **✅ Binance Spot Signal Bot запущен**

## Порты
- Контейнерный порт `8080/tcp` пробрасывается на хост **8181**. Web UI: `http://[HOST]:8181`.

## Отличия от KuCoin‑версии
- Источник данных: Binance REST (`/api/v3/ticker/24hr`, `/api/v3/klines`, `/api/v3/ticker/bookTicker`).
- Символы: внутри — `XXX-USDT`, наружу в Binance — `XXXUSDT` (конвертируется автоматически).
- Фильтр ETF/левередж‑тикеров: `UP/DOWN`, `BULL/BEAR` с окончанием `USDT`.

## Иконки
Новые `icon.png` и `logo.png` (жёлтый фон с белыми свечами).

## Примечания
Используйте на свой страх и риск. Работает как обычный HA‑аддон, оптимально для установки из GitHub‑репозитория.
