# LabscriptAI local chat demo

Single-page local demo. Browser talks to a small pi-agent-core server; that server calls the existing Labscript backend and a thin LogicPass CLI. Not production. Do not deploy.

Binds **127.0.0.1 only**. Do not start if localhost cannot bind. Do not listen on `0.0.0.0`.

## What you do

1. Write an experimental goal. Notes are optional.
2. In chat, pick a robot: **OT-2, Flex, Hamilton, or Tecan**. The server fills a standard deck (tip rack, 96-well plate, reservoir). You can correct the deck later.
3. The agent writes a short SOP, then:
   - **OT-2 / Flex:** Opentrons Python via **8010** when the code service is up, then simulate + analyze + LogicPass.
   - **Hamilton / Tecan:** Plan IR + PyLabRobot checks (no 8010 Python).
   - **OT-2 / Flex fallback:** if 8010 is down or `generate_code` is blocked, the agent emits Plan IR and runs the same PyLabRobot checks. Watch/animation stays unavailable without 8010 analyze commands.
4. **Watch animation** lights only after FinalPass_v2, and only if `session.analyze` from 8010 has commands (Opentrons Python path only).

There is no live robot, no `bash`. Hardware is collected in chat — no deck UI.

## Run

Need a DeepSeek key: `LABSCRIPTAI_DEEPSEEK_API_KEY`, or the existing `LabscriptAI_cloud/.env` (never copied here). Model: `deepseek-v4-flash`. **8010** is required for OT-2/Flex Python generation and Watch; Hamilton/Tecan and OT Plan-IR fallback do not need it.

Optional: `pip install pylabrobot` for Hamilton/Tecan and OT Plan-IR simulation. Missing PyLabRobot is not a pass — checks report the failure.

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
