
#!/usr/bin/with-contenv bash
set -euo pipefail
echo "[INFO] Starting Binance Spot Signals add-on…"
CFG="/data/options.json"
export PYTHONPATH=/opt/app
echo "[INFO] Launching bot with /opt/venv/bin/python -m src.app"
exec /opt/venv/bin/python -m src.app --config "$CFG"
