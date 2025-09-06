#!/bin/sh
set -eu

if [ ! -f /data/config.yaml ]; then
  echo "config.yaml not found in /data. Creating a default one..."
  cat > /data/config.yaml <<'EOF'
symbols: ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT"]
timezone: "Asia/Seoul"
vwap_session_reset: "00:00"
cooldown_minutes_per_symbol: 10
send_startup_message: true
min_alert_level: "conservative"
thresholds:
  near_vwap_sigma: 1.0
  ema_confluence_pct: 0.25
  impulse_body_factor: 1.5
  vol_spike_factor: 1.5
ws_url: "wss://stream.binance.com:9443/stream"
rest_base: "https://api.binance.com"
history_bars: 300
log_level: "INFO"
EOF
fi

if [ -f /data/.env ]; then
  set -a
  . /data/.env
  set +a
fi

export PYTHONPATH=/app
exec python -m src.app --config /data/config.yaml
