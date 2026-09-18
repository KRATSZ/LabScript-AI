# Singapore production snapshot (2026-09-18)

Read-only copy of the live labscriptai.cn site. This branch is a backup only.
Do not merge to `main` or `pi-agent`.

## Live mapping

- Public site: `https://labscriptai.cn` (static, OpenResty)
- Backend: `https://backend.labscriptai.cn` → `127.0.0.1:9002` → container `labscriptai-backend`
- App tree on server: `/root/LabscriptAI_cloud`
- Served frontend: `/opt/1panel/www/sites/labscriptai.cn/index/dist`

## What this branch contains

- `LabscriptAI_cloud` files at repo root (source, docker compose without secrets, frontend `dist`)
- `live-www/` exact files served for labscriptai.cn
- `live-nginx/` vhost + backend proxy conf (certificate *paths* only, no private keys)

## Stripped before git add

- `docker/.env` (present on the live server; not copied here)
- SSL private keys / certs under site `ssl/`
- `node_modules/`, `.git/` from the server tree, `__pycache__`, `*.log`
- Hardcoded API key strings found in two `archive/pylabrobot/` samples (replaced with `YOUR_API_KEY`)

The live site was not stopped, replaced, or redeployed.
