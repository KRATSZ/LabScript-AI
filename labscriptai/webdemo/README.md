# LabscriptAI local chat demo

Single-page local demo. Browser talks to a small pi-agent-core server; that server calls the existing Labscript backend and a thin LogicPass CLI. Not production. Do not deploy.

Binds **127.0.0.1 only**. Do not start if localhost cannot bind. Do not listen on `0.0.0.0`.

## Devices

Pick a **device card** on the start form (required, with a goal). Five cards:

| Card | Deliverable | Animation |
| --- | --- | --- |
| **OT-2** | Python + simulation | Yes (needs 8010 analyze) |
| **Flex** | Python + simulation | Yes (needs 8010 analyze) |
| **Hamilton STAR** | Step JSON + PyLabRobot script | No (software Chatterbox) |
| **Hamilton Vantage** | Step JSON + PyLabRobot script | No (software Chatterbox) |
| **Tecan Fluent** | Step JSON + `.gwl` worklist | No |

One shell: left chat, right Stage / Artifacts / Trajectory. Trajectory is an append-only turn/step/tool log. Live robots stay with the human.

If 8010 is down, OT-2/Flex fall back to the same step table as Hamilton. Downloads stay available; they are marked when checks did not pass. One automatic patch, then the agent stops and talks.

No live robot, no `bash`. No deck UI — a standard deck is assumed (tip rack, 96-well plate, reservoir).

## Checks

Three states, never a silent pass:

- **pass** — simulation + LogicPass both good (Tecan also needs Fluent compile). Watch only lights on OT-2/Flex pass with analyze commands.
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
- Backend (OT Python + simulate + analyze): `127.0.0.1:8010` (`python/code_service.py`)

```bash
cd labscriptai/webdemo && npm test
```

No `0.0.0.0`. Frontend-only: `npm run build`. Server-only: `npm run dev:server`.
