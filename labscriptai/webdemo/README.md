# LabscriptAI local chat demo

Single-page local demo. Browser talks to a small pi-agent-core server; that server calls the existing Labscript backend and a thin LogicPass CLI. Not production. Do not deploy.

Binds **127.0.0.1 only**. Do not start if localhost cannot bind. Do not listen on `0.0.0.0`.

## Behavior

Four robots: **OT-2, Flex, Hamilton, Tecan**. Name one in the goal and generation starts; otherwise the agent asks once which robot, then assumes a standard deck (tip rack, 96-well plate, reservoir).

- **OT-2 / Flex:** Python via **8010** when that service is up; otherwise a step table. Watch/animation is Opentrons-only and needs 8010 analyze commands.
- **Hamilton / Tecan:** step table only. Never Python, never Watch.

Checks are **pass / fail / cannot-verify**. cannot-verify never lights Watch. One automatic patch, then the agent stops and talks. Downloads are always available; they are marked when checks did not pass.

No live robot, no `bash`. No deck UI.

## Run

Need a DeepSeek key: `LABSCRIPTAI_DEEPSEEK_API_KEY`, or the existing `LabscriptAI_cloud/.env` (never copied here). Model: `deepseek-v4-flash`. **8010** is required for OT-2/Flex Python and Watch; Hamilton/Tecan and the OT step-table fallback do not need it.

Optional: `pip install pylabrobot` for Hamilton/Tecan and OT step-table simulation. Missing PyLabRobot is not a pass — checks report cannot-verify.

```bash
cd labscriptai/webdemo
npm install
npm run dev
```

Open http://127.0.0.1:5173

- UI: `127.0.0.1:5173` (Vite)
- Agent server: `127.0.0.1:8787`
- Backend: `127.0.0.1:8010`

```bash
cd labscriptai/webdemo && npm test
```
