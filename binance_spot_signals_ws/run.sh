#!/usr/bin/with-contenv bashio
set -euo pipefail

# Load secrets (Telegram)
if [ -f /addon_configs/binance_spot_signals_ws/.env ]; then
  set -a; . /addon_configs/binance_spot_signals_ws/.env; set +a
elif [ -f /data/.env ]; then
  set -a; . /data/.env; set +a
fi

# Use Supervisor-rendered options.json directly (JSON is valid YAML)
CFG="/data/options.json"

export PYTHONPATH=/opt/app
exec /opt/venv/bin/python -m src.app --config "$CFG"
