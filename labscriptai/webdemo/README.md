# LabscriptAI local chat demo

Single-page local demo. Browser talks to a small pi-agent-core server; that server calls the existing Labscript backend and a thin LogicPass CLI. Not production. Do not deploy.

Binds **127.0.0.1 only**. Do not start if localhost cannot bind. Do not listen on `0.0.0.0`.

## Devices

Pick a **device card** on the start form (required, with a goal). Five cards:

| Card | Deliverable | Animation |
| --- | --- | --- |
| **OT-2** | Python + simulation | Current-protocol OT-2 3D by default; official 2D deck toggle |
| **Flex** | Python + simulation | Official Opentrons deck replay (8010 queued analyze) |
| **Hamilton STAR** | Step JSON + PyLabRobot script | PyLabRobot STARLet visualizer |
| **Hamilton Vantage** | Step JSON + PyLabRobot script | PyLabRobot Vantage visualizer |
| **Tecan Fluent** | Step JSON + `.gwl` worklist | PyLabRobot Freedom EVO geometry (Fluent has no PLR deck yet) |

One shell: left chat, right Stage / Artifacts / Trajectory. Trajectory is an append-only turn/step/tool log. Live robots stay with the human.

If 8010 is down, OT-2/Flex fall back to the same step table as Hamilton. SOP and step JSON remain available for inspection. Executable Python, PyLabRobot scripts and worklists are withheld until the current checks pass. One automatic patch, then the agent stops and talks.

No live robot, no `bash`. A standard deck is assumed (tip rack, 96-well plate, reservoir). OT-2 defaults to its current-protocol 3D scene, with the official Opentrons 2D visualizer available in Stage; Flex keeps the official 2D visualizer plus a 3D entry. Other robots use the PyLabRobot scientific visualizer — not a homemade slot sketch.

## Checks

Explicit user reagent inventories, destination capacity and no-split/no-mix conditions are retained separately from model-authored goals. The parser covers common inventory rows and simple transfer/capacity wording; it is not a general natural-language proof of protocol correctness. Opentrons liquid moves are additionally checked against installed official pipette working ranges and configureForVolume mode in both Python analysis and the Plan fallback. Unknown ranges or ambiguous fallback hardware cannot pass. Hardware substitutions require another confirmation. Standard Hamilton 300 µL tips and Fluent DiTi 200 profiles return cannot-verify below 10 µL until a suitable calibrated low-volume method is provided; 10 µL is the lowest published performance test point used by this demo, not a universal physical minimum.

Three states, never a silent pass:

- **pass** — simulation + LogicPass both good (Tecan also needs Fluent compile). OT Watch lights on OT-2/Flex pass with analyze commands and embeds the official deck in Stage.
- **fail** — a check found a real problem (spill, no tips, compile error, …).
- **cannot verify** — the checker could not run or lacked data (missing PyLabRobot, unknown well capacity, 8010 down, …). Not a pass. Watch stays off.

## Run

Need a DeepSeek key: `LABSCRIPTAI_DEEPSEEK_API_KEY` (or `DEEPSEEK_API_KEY`) in `labscriptai/webdemo/.env`. Model: **`deepseek-flash`**. Copy `.env.example`. Never commit keys. **8010** is the local OT code/analyze service (`python/code_service.py`); `npm run dev` starts it on `127.0.0.1:8010` next to 8787 and 5173. Install `pip install -r python/requirements-code-service.txt` once. If 8010 is down, OT-2/Flex Watch and Python codegen stay off — the UI does not fake them.

Optional: `pip install pylabrobot` for Hamilton/Tecan and OT step-table simulation. Missing PyLabRobot reports cannot-verify, not pass.

```bash
cd labscriptai/webdemo
cp .env.example .env   # set LABSCRIPTAI_DEEPSEEK_* — never commit
pip install -r python/requirements-code-service.txt
npm install
npm test && npm run dev
```

Open http://127.0.0.1:5173

- UI: `127.0.0.1:5173` (Vite)
- Agent server: `127.0.0.1:8787`
- Backend (OT Python + queued analyze + PyLabRobot viz): `127.0.0.1:8010` (`python/code_service.py`)

Analyze matches production: `POST /api/visualizer/analyze/start` then poll `GET /api/visualizer/jobs/{id}` (and `/jobs/{id}`). Sync `POST /api/visualizer/analyze` stays as a fallback.

Official OT replay is npm `@opentrons/protocol-visualization` (source: [Opentrons/opentrons](https://github.com/Opentrons/opentrons)). Do **not** vendor the ~305MB `opentrons-protocol-visualizer-web-slim` tree. At deploy, hang that checkout with `LABSCRIPTAI_VISUALIZER_ROOT` if you still need the old slim animator path.

```bash
cd labscriptai/webdemo && npm test
```

No `0.0.0.0`. Frontend-only: `npm run build`. Server-only: `npm run dev:server`.

## Current-protocol 3D service (maintainers)

The web server forwards accepted OT-2/Flex analyses to `FLEX3D_URL` (default `http://127.0.0.1:8791`). The renderer is the separate `virtual-lab` workspace's `sim.web_player`; it is **not bundled in this repository**. OT-2 requires that service's OT-2-capable version (`robotType: "OT-2 Standard"`); Flex uses `"OT-3 Standard"`. Unsupported, mismatched or unfinished sessions return a clear error instead of loading an example. The 2D toggle remains available if 3D is unavailable.

`npm run dev` can find a sibling `virtual-lab` checkout; maintainers may override its path with `LABSCRIPTAI_PLAYER_ROOT`. It uses the same `LABSCRIPTAI_PYTHON` interpreter as the code service, which must also contain the renderer dependencies. No browser-side setup is required.

The accompanying [OT-2 renderer patch](renderer-patches/ot2-base-clearance.patch) belongs to that separate workspace: its old solid base band covered low plates in the main view. From the renderer root, first run `patch --dry-run -p1 < /absolute/path/to/ot2-base-clearance.patch`, then apply with `patch -p1 < /absolute/path/to/ot2-base-clearance.patch` and restart the service. Substitute the actual absolute patch path; no Git checkout is needed. The patch replaces the slab with a surrounding ring without moving the deck, wells or pipette targets. This PR's 3D evidence uses that patch; merging only the web code does not update the renderer or deploy the website.
