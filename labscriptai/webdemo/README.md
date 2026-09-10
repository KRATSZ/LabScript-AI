# LabscriptAI local chat demo

Single-page local demo. Browser talks to a small pi-agent-core server; that server calls the existing Labscript backend and a thin LogicPass CLI. Not production. Do not deploy.

Binds **127.0.0.1 only**. Do not start if localhost cannot bind. Do not listen on `0.0.0.0`.

## What you do

1. Write an experimental goal. Notes are optional.
2. In chat, say the robot: **OT-2 or Flex**. A common deck (tip rack, 96-well plate, reagent reservoir) is enough.
3. The agent writes a short SOP, then Opentrons Python via **8010**, then runs simulate + analyze + LogicPass.
4. **Watch animation** lights only after FinalPass_v2, and only if `session.analyze` from 8010 has commands.

There is no live robot, no `bash`. Hardware and robot are collected in chat — no deck UI.

Internal: extra tools (`emit_plan`, Hamilton/Tecan presets) may exist in the server. The demo path is Opentrons Python so the deck animator can play.

## Run

```bash
cd labscriptai/webdemo
npm install
npm run dev
```

Open http://127.0.0.1:5173

- UI: `127.0.0.1:5173` (Vite)
- Agent server: `127.0.0.1:8787`
- Backend: `127.0.0.1:8010`

Need a DeepSeek key: `LABSCRIPTAI_DEEPSEEK_API_KEY`, or the existing `LabscriptAI_cloud/.env` (never copied here). Model: `deepseek-v4-flash`.

```bash
cd labscriptai/webdemo && npm test
```
