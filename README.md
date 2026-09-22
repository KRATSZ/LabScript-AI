# LabscriptAI

LabscriptAI turns a liquid-handling protocol written in ordinary language into robot-ready files, checks them in simulation, and — on a live Opentrons Flex — watches the run. When a command fails (no tip in the well, empty reservoir, and similar), it proposes a recovery. A separate gate, not the language model, decides whether that recovery may run, must wait for a person, or must stop.

[![Canonical release](https://img.shields.io/github/v/tag/KRATSZ/LabScript-AI?label=v1.0-canonical)](https://github.com/KRATSZ/LabScript-AI/releases/tag/v1.0-canonical)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.17697326.svg)](https://doi.org/10.5281/zenodo.17697326)

**Browser demo (no robot):** [labscriptai.cn](https://labscriptai.cn/)

---

## Who this is for

People who already run, or are about to run, **Opentrons OT-2 / Flex**, **Hamilton STAR / Vantage**, or **Tecan Fluent** liquid handlers — automation engineers, core-lab staff, iGEM and synbio teams.

It is not a general lab chatbot. It does not replace a human on a live deck.

## What it does in practice

**At the desk (authoring).** You give a goal plus your SOP and hardware setup. LabscriptAI writes a protocol package — Python for Opentrons, or a step list / worklist for Hamilton and Tecan — then a simulator and a logic checker try to catch empty sources, missing tips, and volume mistakes before anything moves.

**On the robot (runtime, Opentrons).** The same agent can play a package that already passed simulation, watch the command queue, and recover from a small set of known failures. Camera frames and pipette-pressure traces are extra evidence only. What the controller reports is the deck of record.

Those are two loops on purpose. Authoring must not move hardware. Runtime must not silently rewrite the protocol.

![Pipeline from intent through package authoring, simulation, physical execution, and memory, with a separate authoring loop and runtime loop](assets/fig-a-architecture.png)

The figure is the product shape: a goal becomes a package you can simulate, then (if you choose) a physical run. The language model sits in the middle. Around it, the figure shows human SOP confirmation, biosecurity screening, and approval checkpoints. **This clone implements the authoring/runtime loops and the robot gates.** Sequence-level biosecurity review is still an operator responsibility — it is not an automated feature of `git clone`.

## Authoring is not “chat until the traceback goes away”

A typical LLM session looks like: generate Python → paste it into Opentrons or PyLabRobot → hit `LabwareNotFoundError` → paste the traceback back → get a new script that is wrong in a different place.

LabscriptAI keeps the model inside a closed authoring loop: plan → write `protocol.py` → simulate → targeted patch → repeat until the simulator passes. You get a package (`protocol.py`, manifests, a trace), not a one-off code block. On a live run, sensing and recovery are a second loop with their own gate.

![Side-by-side of manual LLM trial-and-error versus LabscriptAI closed-loop authoring, then protocols.io to code to robotic liquid handling on Flex, OT-2, Tecan Fluent, and Hamilton Vantage](assets/fig-b-authoring-vs-manual.png)

Same kind of request (here: an iGEM fluorescein serial dilution). Left: you are the debugger. Right: the simulator is. Below: that class of protocol authored toward Flex, OT-2, Tecan Fluent, and Hamilton Vantage.

## How a robot action is allowed

Every live action goes through a three-way gate:

| Gate | Meaning |
| --- | --- |
| **allow** | On the safe list; may run now |
| **ask** | A person has to confirm (or name a spare slot, a spare source, …) |
| **suspend** | Stop. Hardware faults, deck collisions, and unknowns always land here |

The model may **propose**. It does not get to **release** motion. A failed simulation blocks unattended play. After a few targeted patches, retries stop instead of looping forever.

![Execution-aware agent harness: authoring with a human SOP checkpoint and simulation gate, then runtime observe–propose–gate–act with allow, ask, or suspend](assets/fig-c-execution-harness.png)

Authoring (top) ends in a validated package. Runtime (bottom) is observe → propose → gate → act → write the result back. Orange is human, teal is the model, white is ordinary deterministic code.

## When a command fails on the deck

The run is a command queue. A failure (for example `pickUpTip` / “No Tip Detected”) does not let the model invent a jog. The agent classifies the event, looks up a playbook, and submits a **candidate** action to the same gate.

Vision (on-deck camera, detection overlay) and pressure traces can support a decision. They never override the controller.

If a similar case was already reviewed — “fluorescein stock empty, spare in A4” — that memory can make the next substitution faster. It still goes through the gate.

![Failed command in the execution queue, vision and pressure as advisory evidence, and a live recovery path through the gatekeeper](assets/fig-d-recovery.png)

Failed command → candidate action → allow / ask / suspend. HTTP and the robot API are the source of truth; camera and pressure are advisory.

Always stop and call a person for **hardware fault**, **deck collision**, and **unknown**. Also stop when the enforced tip budget cannot finish the run, the time window has expired, or a sample-contaminated tip would enter common stock.

Do not drive the same robot from this agent and a second HTTP client at the same time.

Before a live Flex, read:

- [`labscriptai/plugins/skills/safety-brief.md`](labscriptai/plugins/skills/safety-brief.md)
- [`labscriptai/plugins/skills/error-taxonomy.md`](labscriptai/plugins/skills/error-taxonomy.md)
- [`labscriptai/plugins/skills/recovery-playbooks.md`](labscriptai/plugins/skills/recovery-playbooks.md)

## Robots this repository actually supports

| Robot | Authoring in this repo | Live run and recovery |
| --- | --- | --- |
| **Opentrons Flex** | Python protocol + Opentrons simulation | Yes — this is the documented live path (`labscriptai chat --robot …`) |
| **Opentrons OT-2** | Same Python path; official deck replay in the web demo | Same robot-server port (`:31950`); Flex is the live recovery target the playbooks were written for |
| **Hamilton STAR** | Step JSON + PyLabRobot script | Not live-controlled here |
| **Hamilton Vantage** | Step JSON + PyLabRobot script | Not live-controlled here |
| **Tecan Fluent** | Step JSON + `.gwl` worklist | Not live-controlled here |

The **local web demo** is the multi-robot authoring UI (device card + goal, downloads, on-screen deck). **`labscriptai chat`** is Flex-oriented authoring plus live Opentrons control. Live motion is not something the web demo does.

![Flex deck hardware, iGEM / distribution-kit workflows, and kit-assembly plate maps](assets/fig-e-applications.png)

Where this has been used: a Flex station, transformation / culture / kit-assembly / extraction workflows, and iGEM parts-kit plate mapping. The figure is the evidence; this README is not the paper.

## Run it

You need **Python 3.10+**. The Opentrons robot backend also needs **Node 18+**. The default model is DeepSeek (`DEEPSEEK_API_KEY`). `labscriptai chat --provider offline` smokes the CLI without an API key.

### Browser demo (no robot)

Hosted: [labscriptai.cn](https://labscriptai.cn/)

Or locally. The demo binds **127.0.0.1 only**.

```bash
cd labscriptai/webdemo
cp .env.example .env          # set LABSCRIPTAI_DEEPSEEK_API_KEY
pip install -r python/requirements-code-service.txt
# optional, for Hamilton/Tecan simulation:
# pip install pylabrobot
npm install
npm run dev
```

Open http://127.0.0.1:5173

That starts the UI (`5173`), the agent server (`8787`), and the Opentrons analyze service (`8010`). If `8010` is down, OT-2/Flex still give you a step table and downloads; they will not pretend the official deck replay passed. Checks are **pass**, **fail**, or **cannot verify** — cannot-verify is not a pass.

Details: [`labscriptai/webdemo/README.md`](labscriptai/webdemo/README.md).

### CLI (desk, or a live Opentrons)

The installable package is **`labscriptai/`**. Use a fresh virtualenv. Do not install a second tree that also ships a `labscriptai` console script.

```bash
git clone https://github.com/KRATSZ/LabScript-AI.git
cd LabScript-AI/labscriptai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "opentrons>=7,<9"   # Opentrons simulation; doctor warns if this is missing
pip install -e ".[dev]"         # optional: pytest

cd plugins/mcp/opentrons-mcp && npm install && cd -

# Put this in a .env at the repo root or in labscriptai/:
#   DEEPSEEK_API_KEY=...
#   ROBOT_IP=192.168.x.x     # optional until you talk to a robot

labscriptai doctor                 # toolchain; add --robot <IP> to ping :31950/health
labscriptai chat                   # default: DeepSeek
labscriptai chat --provider offline
```

`labscriptai chat` is the operator entry. `doctor` is only a health check.

On a live run you can also:

```bash
labscriptai recover --robot <IP> --run-id <ID>
labscriptai daemon  --robot <IP> --run-id <ID>
```

`recover` is one recovery turn. `daemon` polls for a failed command (or an outbox wake) and runs the same loop. When the process is non-interactive, **ask** becomes **suspend**.

Optional env: `LABSCRIPTAI_WORKSPACE`, `LABSCRIPTAI_MCP_INDEX` (override the robot backend `index.js`), `ROBOT_IP`.

`plugins/mcp/opentrons-mcp/` is the **robot backend** for chat. It is not a Cursor plugin and not a second CLI.

Without a Flex, you can still exercise recovery against a local fake robot:

```bash
python -m labscriptai.fake_robot --host 127.0.0.1 --port 31950 --scenario tip_missing_budget_block
labscriptai doctor --robot 127.0.0.1
```

See [`labscriptai/fake_robot/README.md`](labscriptai/fake_robot/README.md).

```bash
cd labscriptai && pytest -q
```

## What's in the tree

```
labscriptai/
  agent/                     chat / recover / daemon / doctor
                             (five tools: bash, edit, robot, memory, skill)
  benchmark/logicpass/       logic checker used during authoring
  planir/                    Hamilton/Tecan step plans + simulation
  fake_robot/                local stand-in for Opentrons robot-server
  plugins/skills/            playbooks the agent loads on demand
  plugins/mcp/opentrons-mcp/ Node backend for live Opentrons
  webdemo/                   local browser demo
  tests/
```

Skills and MCP sources ship in the package; `node_modules/` does not. Run `npm install` after clone.

## Citation

- **Code:** [github.com/KRATSZ/LabScript-AI](https://github.com/KRATSZ/LabScript-AI)
- **Benchmark / shard data:** [Zenodo 10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)

## License

MIT
