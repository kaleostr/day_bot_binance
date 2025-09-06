# Vyacheslav — Home Assistant Add-ons

Этот репозиторий — источник аддонов для Home Assistant.

## Подключение репозитория в Home Assistant
1. **Settings → Add-ons → Add-on Store → ⋮ → Repositories → Add** — вставьте URL этого репозитория GitHub.
2. Найдите **Binance Spot Signals (WebSocket)** → **Install**.
3. Откройте вкладку **Configuration** аддона и заполните параметры (ниже).

## CI/CD в GHCR (готово)
В репозитории уже добавлен workflow `.github/workflows/build.yml`, который при пуше в ветку `main/master` собирает и публикует Docker-образы в **GHCR**.

**Чтобы Home Assistant тянул предсобранный образ:**
- В файле `binance_spot_signals_ws/config.yaml` раскомментируйте строку `image:` и замените `OWNER` на ваш GitHub-ник/организацию:
  ```yaml
  image: "ghcr.io/OWNER/{arch}-addon-binance_spot_signals_ws"
  ```
- В репозитории GitHub включите права workflow-токена: **Settings → Actions → General → Workflow permissions → Read and write permissions**.
- После первой сборки зайдите в GitHub → **Packages** → найдите пакет `aarch64-addon-binance_spot_signals_ws` → **Package settings** → **Change visibility** → **Public**.
- В Home Assistant откройте **Add-on Store → ⋮ → Check for updates** → откройте аддон → **Rebuild/Update**.

> Если оставить `image:` закомментированным — Supervisor будет собирать локально (Local add-on).
