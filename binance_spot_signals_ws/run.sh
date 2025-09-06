#!/usr/bin/with-contenv bashio
set -euo pipefail

# Read add-on options from /data/options.json using bashio
SYMBOLS=$(bashio::config 'symbols' || true)
TIMEZONE=$(bashio::config 'timezone' || echo "Asia/Seoul")
VWAP_RESET=$(bashio::config 'vwap_session_reset' || echo "00:00")
COOLDOWN=$(bashio::config 'cooldown_minutes_per_symbol' || echo 10)
SEND_STARTUP=$(bashio::config 'send_startup_message' || echo true)
MIN_LEVEL=$(bashio::config 'min_alert_level' || echo "conservative")
WS_URL=$(bashio::config 'ws_url' || echo "wss://stream.binance.com:9443/stream")
REST_BASE=$(bashio::config 'rest_base' || echo "https://api.binance.com")
HISTORY_BARS=$(bashio::config 'history_bars' || echo 300)
LOG_LEVEL=$(bashio::config 'log_level' || echo "INFO")

# Persist runtime config for the Python app
CFG=/data/config.yaml
cat > "$CFG" <<EOF
symbols: ${SYMBOLS}
timezone: "${TIMEZONE}"
vwap_session_reset: "${VWAP_RESET}"
cooldown_minutes_per_symbol: ${COOLDOWN}
send_startup_message: ${SEND_STARTUP}
min_alert_level: "${MIN_LEVEL}"
ws_url: "${WS_URL}"
rest_base: "${REST_BASE}"
history_bars: ${HISTORY_BARS}
log_level: "${LOG_LEVEL}"
EOF

# Source optional secrets from addon_config (preferred) or /data/.env for legacy
if [ -f /addon_configs/binance_spot_signals_ws/.env ]; then
  set -a; . /addon_configs/binance_spot_signals_ws/.env; set +a
elif [ -f /data/.env ]; then
  set -a; . /data/.env; set +a
fi

export PYTHONPATH=/opt/app
exec python3 -m src.app --config "$CFG"
