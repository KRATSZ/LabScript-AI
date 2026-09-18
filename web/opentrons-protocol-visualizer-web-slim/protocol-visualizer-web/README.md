# Protocol Visualizer Web

Upload an Opentrons Python (or JSON) protocol in the browser, run **`opentrons.cli analyze`** on the server, and replay the resulting command list as an on-deck animation.

This packages:

1. **FastAPI backend** — multipart upload with optional labware JSON, **RTP values** (JSON), **RTP CSV** files + **mapping JSON**, and `check`. Analysis is **queued** via `POST /api/analyze/start` and polled with `GET /api/analyze/jobs/{job_id}` (the web UI uses this path). A synchronous `POST /api/analyze` remains for simple clients.
2. **Vite + React client** — adapted from the desktop app’s Protocol Visualization UI (deck replay + timeline).
3. **Optional MCP server** — stdio tool `analyze_opentrons_protocol` for agents (`uv sync --extra mcp`, then `uv run protocol-visualizer-mcp`).

## Prerequisites

- Monorepo **Node** / **Yarn** (see root `.nvmrc`).
- **`api/.venv`** with Opentrons installed (run `make -C api setup` from the monorepo root). The API process uses `api/.venv/bin/python` by default to run `python -m opentrons.cli analyze`.
- **uv** for the Python app in this directory.

Override the interpreter if needed:

```bash
export OT_ANALYZE_PYTHON=/path/to/python-with-opentrons
```

## Setup

```bash
cd protocol-visualizer-web
make setup          # uv sync
make setup-client   # yarn in client/
```

From the monorepo root (recommended for workspace links):

```bash
yarn install
```

Ensure the analyzer venv exists at the repo root:

```bash
make -C api setup
```

## Run (development)

Terminal 1 — API:

```bash
cd protocol-visualizer-web
make dev-api
```

Terminal 2 — UI (proxies `/api` and `/health` to port 8765):

```bash
cd protocol-visualizer-web
make dev-client
```

Open `http://127.0.0.1:5177`, choose or drag a `.py` or `.json` protocol, then click **生成动画** (Generate animation).

### 如何本地运行（中文速查）

1. **准备环境（在 monorepo 根目录）**
   - Node 版本与根目录 `.nvmrc` 一致（例如 `fnm use` / `nvm use`）。
   - 安装 JS 依赖（含 workspace 链接）：`yarn install`
   - 安装分析器用的 Python 环境：`make -C api setup`（生成 `api/.venv`，内含 `opentrons`）

2. **安装本工具**
   ```bash
   cd protocol-visualizer-web
   make setup           # Python：uv sync
   make setup-client    # 前端：client 目录 yarn install
   ```

3. **启动（两个终端）**
   - 终端 A — 后端 API（默认 `127.0.0.1:8765`）：
     ```bash
     cd protocol-visualizer-web
     make dev-api
     ```
   - 终端 B — 前端（默认 `http://127.0.0.1:5177`，并把 `/api` 代理到 8765）：
     ```bash
     cd protocol-visualizer-web
     make dev-client
     ```

4. **浏览器** 打开 `http://127.0.0.1:5177` 即可。

若分析失败，确认 `api/.venv` 已就绪，或设置 `OT_ANALYZE_PYTHON` 指向已安装 Opentrons 的解释器。

### CORS

By default the API allows only local dev origins (`http://127.0.0.1:5177`, `http://localhost:5177`), not `*`.

**Production:** set `PV_CORS_ORIGINS` to your real frontend origin(s), comma-separated (no spaces), for example:

```bash
export PV_CORS_ORIGINS=https://viz.example.com,https://www.example.com
```

`make dev-api` also sets `PV_CORS_ORIGINS` explicitly for the Vite dev port.

### Embedded in LabScript AI

The client can run inside the LabScript AI workflow as the fifth step after Simulation.
When embedded, the parent page sends the generated protocol source through `postMessage`
using message type `labscriptai:set-protocol`. The client converts that source into a
virtual `.py` file and can start analysis automatically.

By default, embedded messages are accepted from:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:4173`
- `http://127.0.0.1:4173`
- `http://labscriptai.cn`
- `https://labscriptai.cn`
- `https://www.labscriptai.cn`

Set `VITE_EMBED_PARENT_ORIGINS` on the visualizer client to override the allowed parent
origins, comma-separated. Set `VITE_PROTOCOL_VISUALIZER_URL` on the LabScript AI frontend
to point the fifth step iframe at a non-default visualizer URL.

## RTP and CSV uploads

- **`rtp_values`** — form field: JSON object of primitive RTP values (same as `opentrons analyze --rtp-values`).
- **`rtp_csv`** — one or more uploaded CSV files (multipart, repeated field name `rtp_csv`).
- **`rtp_files_map`** — form field: JSON object mapping RTP variable names to the **uploaded file’s basename**, e.g. `{"liquids": "liquids.csv"}`. The server resolves these to temp paths and passes `--rtp-files` to the CLI.

If you upload any `rtp_csv` files, `rtp_files_map` is required.

## API summary

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/analyze/start` | Start async job; returns `{ "job_id": "..." }` |
| GET | `/api/analyze/jobs/{job_id}` | `pending` \| `running` \| `completed` \| `failed`; `result` when completed |
| POST | `/api/analyze` | Same body as start, but waits until analysis finishes (may time out behind proxies) |

## Production-style run

Build the client, then serve static files with any static host and point `VITE_API_BASE` at your API origin, **or** mount `StaticFiles` from FastAPI (not included by default).

```bash
cd client && yarn build
```

## MCP (agents)

```bash
cd protocol-visualizer-web
make setup-mcp
uv run protocol-visualizer-mcp
```

Tool: **`analyze_opentrons_protocol`** — arguments: `protocol_source` (string), `filename` (e.g. `my_protocol.py`). Returns analyzer JSON as a string. For RTP values or CSV-backed RTP parameters, use the HTTP API (`rtp_values`, `rtp_files_map`, `rtp_csv` uploads).

## Limitations

- Job store is **in-memory** (single process); restarts lose jobs. Scale-out would need Redis or similar.
- Very large uploads still load into memory once before analysis.
