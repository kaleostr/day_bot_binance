CI/CD готов.
- Права: Settings → Actions → General → Workflow permissions → Read and write permissions.
- Раскомментируйте `image:` в `binance_spot_signals_ws/config.yaml` и замените OWNER.
- Первый пуш в main соберёт и запушит образы:
  ghcr.io/OWNER/aarch64-addon-binance_spot_signals_ws:1.7.1 и :latest
- В GHCR сделайте пакет Public (иначе Supervisor не подтянет).
- В HA: Add-on Store → ⋮ → Check for updates → Update/Rebuild.
