
#!/usr/bin/with-contenv bashio
set -euo pipefail
bashio::log.info "Starting Binance Spot Signals add-on…"
CFG="/data/options.json"
export PYTHONPATH=/opt/app
bashio::log.info "Launching bot with /opt/venv/bin/python -m src.app"
exec /opt/venv/bin/python -m src.app --config "$CFG"
