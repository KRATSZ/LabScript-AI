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
pip install -r renderer/requirements.txt
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

`npm run dev` starts the bundled `renderer/sim/web_player.py` on `127.0.0.1:8791`.
The web server forwards the current accepted analysis to that service. Robot
identity selects `OT-2 Standard` or `OT-3 Standard` (Flex); unfinished,
mismatched and unsupported sessions return an error and retain the current
protocol. The 2D view remains available when the 3D service is unavailable.

Cold model preparation has a 45-second total limit, including analysis loading.
An interrupted request shows a readable error and a direct retry button. Model
eviction releases graphics resources in their owning context so switching
between protocols keeps overview and close-up frames intact.

Install `renderer/requirements.txt` in the same `LABSCRIPTAI_PYTHON` environment
as the code service. Python 3.11, Opentrons 8.8.2 and MuJoCo 3.17 are the tested
combination. OT-2 Python input uses the public `opentrons analyze --check` CLI
through `OPENTRONS_PYTHON` or the current interpreter. Existing analysis JSON
can be replayed directly. A normal checkout includes the runtime and assets;
`LABSCRIPTAI_PLAYER_ROOT` is an explicit development override.

Generated models and frames use the ignored `webdemo/.local/renderer` cache.
`LABSCRIPTAI_RENDERER_EXPORT` selects another writable output directory. No
browser-side renderer configuration is required.

The OT-2 model preserves official deck/command coordinates while refining the
GEN2 single/eight-channel shells, model-specific nozzles, open translucent tips,
Z-mount connections and GEN1 thermocycler outer lid. Its envelope follows the
2019 manufacturer reference: 154 mm closed and 312 mm open; hinge and small
part dimensions remain estimates. The planner clears the lid's XY sweep
before opening or closing it. The isolated Flex runtime retains its modules,
stacked adapters, tube racks, waste chute and gripper handling.

Both runtimes track liquid separately from air gaps, preserve explicit waits
and thermal holds, and check positional commands and sampled moving clearance
before serving a preview. Unknown actions are rejected. Flex `touchTip` remains
an explicit text-only action with a warning. Missing inventories, manual pause
markers and possible overlap between coarse static definition envelopes appear
as range warnings and make validation `partial`. Motion and thermal ramp
durations are illustrative; the renderer does not certify physical execution.

Run the maintained regression tests from `labscriptai/webdemo/renderer`:

```bash
OT2_GEOMETRY=1 PYTHONPATH=. /path/to/qa-venv/bin/python -m unittest discover -s tests -p 'test_*protocol_regression.py' -v
```

The OT-2 matrix includes 27 positive replay protocols, one unsupported manual
move, and one short-tip/deep-tube clearance negative. Every input is freshly
analyzed by the official SDK; independent intent oracles check the liquid
results. Flex tests cover gas/liquid order, absolute moves, waits, manual
pauses, waste, modules and gripper moves. See [test details](renderer/tests/README.md).

After reviewing a source-runtime change, refresh the snapshot with:

```bash
node scripts/sync-renderer.mjs --source /absolute/path/to/virtual-lab
node --test scripts/renderer-root.test.mjs
```

The script copies the runtime and required assets in [SOURCE.json](renderer/SOURCE.json)
and applies portable output/interpreter defaults. Generated models, reference
photos and authoring files are excluded.

The [earlier patches](renderer-patches/) and [UX records](UX_REVIEW.md) remain
historical evidence; they are not applied to the bundled renderer. The historical
five-module catalogue has overlapping temperature-module envelopes and is a
layout-warning example, not an accepted hardware arrangement. A fixed
[80 µL analysis](renderer-patches/ot2-80ul-visual-fixture.analysis.json) can also be
replayed without a generation API call. Source provenance and remaining visual
limits are recorded in [renderer/README.md](renderer/README.md). Repository
changes do not deploy the website.
