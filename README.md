# LabscriptAI

**An execution-aware agent harness for liquid-handling robots.**

LabscriptAI turns natural-language protocols into validated robot scripts and supports bounded recovery on a live Opentrons Flex, subject to deterministic authorization and human oversight.

[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.22054311.svg)](https://doi.org/10.5281/zenodo.22054311)

[Try the web demo (no hardware needed)](https://labscriptai.cn/) · [Run locally](#getting-started) · [Project overview](#project-overview) · [Read the preprint (v2)](https://www.biorxiv.org/content/10.1101/2025.09.30.679666v2)

## Live Flex Recovery

A tip-pickup failure on an Opentrons Flex: without runtime perception, the run remains paused; with the full system, the failure is detected, a recovery action is selected, and the run resumes. This is one filmed comparison, not a claim that every fault is recoverable.

<p align="center">
  <img src="assets/live-flex-tip-recovery.gif" alt="Opentrons Flex tip-pickup failure comparison: run stays paused without runtime perception; with LabscriptAI, the failure is detected and the run recovers" width="800" />
</p>

The clip shows the robot outcome, not the underlying authorization log. Recovery proposals are checked by a deterministic gatekeeper; actions that need confirmation wait for an operator, and unsafe or unknown cases stop.

## How It Works

1. **Author and verify:** Turn a human-confirmed procedure into a platform-specific script, then use simulation and validation feedback to repair errors before execution.
2. **Observe the live run:** Track controller-reported command and run state; camera images and pressure traces provide advisory evidence but cannot override controller state.
3. **Recover within bounds:** Propose an action for a failed command. The gatekeeper decides `allow`, `ask`, or `suspend`; only authorized actions reach the robot.

## Project Overview

<p align="center">
  <img src="assets/intro-video-preview.gif" alt="Animated overview of LabscriptAI" width="640" />
</p>

---

## System Overview

LabscriptAI separates protocol creation at your desk from live execution on the robot deck:

<img src="assets/fig-a-architecture.png" alt="System architecture and end-to-end workflow" width="680" />

- **The Authoring Loop (Desk):** Converts your natural-language intent and SOP into a verified protocol package (`protocol.py`, step manifests, and execution traces). A platform simulator catches labware mismatches, volume overflows, and trajectory issues before anything touches hardware.
- **The Runtime Loop (Robot):** Runs only validated packages. While the robot executes commands, the agent tracks live status. If a command fails, the agent looks up recovery playbooks and proposes a fix.
- **Human-in-the-Loop & Safety Gates:** Operators confirm initial SOP plans and review edge-case recoveries. Critical safety rules—like collision prevention and tip budget limits—are hardcoded and deterministic.
- *A note on biosecurity:* While the architecture supports biosecurity screening and containment checkpoints (as illustrated above), sequence-level biosecurity screening in practical deployment is the operator's responsibility; it is not automated by this code repository.

---

## Closed-Loop Authoring vs. Manual Chat Debugging

Most LLM coding tools leave you acting as the manual error-fetcher:

<img src="assets/fig-b-authoring-vs-manual.png" alt="Manual trial-and-error versus LabscriptAI closed-loop authoring" width="620" />

Instead of handing you raw code to debug yourself:
- **Plan & Generate:** The agent structures the SOP into formal steps (volumes, labware slots, pipetting mechanics).
- **Simulate & Verify:** The script is immediately run against Opentrons simulation and the `LogicPass` validation engine.
- **Targeted Self-Correction:** When simulation fails (e.g., missing labware definition or invalid tip rack slot), the agent applies focused search/replace patches directly to the protocol file and re-simulates.
- **Ready-to-Run Packages:** You receive complete, downloadable protocol packages with verified step tables and manifests rather than a one-off code snippet.

---

## Safety Architecture: The Allow / Ask / Suspend Gate

LLMs are creative, but physical lab hardware cannot tolerate hallucinated movements or rogue jogs. In LabscriptAI, the language model can only submit **candidate actions**. Every action must pass through an independent, deterministic gatekeeper:

<img src="assets/fig-c-execution-harness.png" alt="Execution-aware agent harness with the three-way gate" width="680" />

| Gate Decision | What It Means | Examples |
|---|---|---|
| **`allow`** | Safe and pre-authorized. May execute immediately without operator interruption. | Retrying tip pickup from the next valid well in the rack; switching to a pre-mapped spare buffer well. |
| **`ask`** | Needs human confirmation. The system pauses and prompts the operator to approve or provide details. | Selecting an unconfirmed substitute reagent; ambiguous sensor readings. *(In non-interactive daemon mode, `ask` automatically upgrades to `suspend`.)* |
| **`suspend`** | Immediate halt. Execution stops safely to protect hardware and samples. | Physical deck collision; hardware actuator faults; tip budget exhausted; risk of a contaminated tip entering common stock; unknown errors. |

---

## Real-Time Monitoring and Recovery

On a live Opentrons Flex, runs proceed through an active command queue:

<img src="assets/fig-d-recovery.png" alt="Live command monitoring, advisory sensor tiers, and recovery decision flow" width="680" />

### Tiered Sensor Stack
To avoid hallucinations or sensor misreads causing hardware errors, inputs are organized into distinct trust tiers:
1. **Tier 1 & 2 (Authoritative):** Robot controller HTTP status and MCP state. What the controller reports is the ground truth of the deck.
2. **Tier 3 (Advisory Evidence):** On-deck camera captures (with YOLO/VLM component detection overlays) and pipette pressure traces. These provide helpful diagnostic context for the agent, but they can never override controller telemetry or force a resume.

### Playbooks and Case Memory
When a command fails (such as an empty reservoir or unseated tip):
- The agent classifies the error against a standardized taxonomy (`labscriptai/plugins/skills/error-taxonomy.md`).
- It selects a recovery playbook (`labscriptai/plugins/skills/recovery-playbooks.md`) to craft a safe candidate response.
- If a similar issue was resolved previously—for example, switching from an empty fluorescein well at A3 to a reserve well at A4—the system recalls that case memory to streamline the recovery while still verifying through the gatekeeper.

---

## Supported Robots: Live Execution vs. Authoring-Only

Different robots have different interfaces and access levels. Here is exactly what this repository supports:

| Robot Platform | Authoring & Verification | Deck Replay ("Watch") | Live Control & Recovery |
|---|---|---|---|
| **Opentrons Flex** | Full Python protocol generation + Opentrons simulator | Yes (web demo Stage view) | Yes — documented live path via HTTP API (`:31950`) with automated recovery playbooks |
| **Opentrons OT-2** | Full Python protocol generation + Opentrons simulator | Yes (web demo Stage view) | Yes — connects via port `:31950`; recovery playbooks were primarily developed for Flex |
| **Hamilton STAR** | Step JSON + runnable PyLabRobot (`.py`) scripts | No | Authoring-only (no live hardware driver in this repo) |
| **Hamilton Vantage** | Step JSON + runnable PyLabRobot (`.py`) scripts | No | Authoring-only (no live hardware driver in this repo) |
| **Tecan Fluent** | Step JSON + `.gwl` worklists | No | Authoring-only (no live hardware driver in this repo) |

### The "Watch" Deck Visualizer
In the web demo, **Watch** is the built-in Opentrons deck visualizer. When an OT-2 or Flex protocol passes simulation, the Watch button appears on the Stage tab. It renders the deck layout, labware placements, and lets you scrub through each pipetting step. (Because Hamilton and Tecan use distinct proprietary runtimes, their protocols output clean step tables and script downloads without web deck playback).

---

## Real-World Applications

Research deployments include standardized characterization of 854 GFP designs from 171 student teams across the 2025 and 2026 CAPE rounds, as well as preparation and quality assurance of 531 genetic parts for the 2025 iGEM Distribution Kit. These are study-wide workflows, not features fully automated by this repository:

<a href="assets/fig-5-igem-distribution-kit.png">
  <img src="assets/fig-5-igem-distribution-kit.png" alt="Figure 5 from the September 2026 manuscript: Tecan Fluent deck, iGEM Distribution Kit workflow, quality assurance, and plate mapping" width="760" />
</a>

Workflows demonstrated include:
- *E. coli* transformation and outgrowth setup
- Clonal culture isolation and liquid cultivation
- Bead-based plasmid DNA extraction
- High-throughput distribution kit assembly: taking sequencing, concentration, and inventory manifests to calculate volume normalizations and map liquid transfers across 96-well and 384-well plates.

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** (required for the Opentrons robot backend and web demo)
- An API key for DeepSeek (`DEEPSEEK_API_KEY`) or an OpenAI-compatible provider.

---

### Option 1: Browser Web Demo (Recommended for protocol authoring)

You can try the hosted version directly at [labscriptai.cn](https://labscriptai.cn/).

To run the web interface locally on your machine (binds strictly to `127.0.0.1`):

```bash
cd labscriptai/webdemo
cp .env.example .env          # Add your LABSCRIPTAI_DEEPSEEK_API_KEY
pip install -r python/requirements-code-service.txt
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

This command starts:
- The frontend UI on port `5173`
- The web agent server on port `8787`
- The local Opentrons code analyze service on port `8010` (used for Python simulation and generating Watch deck playback)

For more details on web demo configuration, see [`labscriptai/webdemo/README.md`](labscriptai/webdemo/README.md).

---

### Option 2: CLI Agent (Desk authoring & live Opentrons control)

Install the package in an isolated virtual environment:

```bash
git clone https://github.com/KRATSZ/LabScript-AI.git
cd LabScript-AI/labscriptai

python3 -m venv .venv && source .venv/bin/activate
pip install -e .
pip install "opentrons>=7,<9"   # Required for local Opentrons simulation
pip install -e ".[dev]"         # Optional: for running pytest

# Install the Node-based Opentrons robot backend
cd plugins/mcp/opentrons-mcp && npm install && cd -
```

Configure environment variables (in a `.env` file or exported in your shell):
```bash
DEEPSEEK_API_KEY=your_api_key_here
ROBOT_IP=192.168.x.x           # Optional until connecting to physical hardware
```

#### Run Health Check
Verify your environment, dependencies, and optional robot connectivity:
```bash
labscriptai doctor                 # Check toolchain, Node, Python, and API key
labscriptai doctor --robot <IP>    # Also ping the robot's :31950/health endpoint
```

#### Start Interactive Chat
```bash
labscriptai chat                   # Interactive agent (default: DeepSeek)
labscriptai chat --provider offline # Smoke test the REPL without making API calls
```

#### Live Recovery and Daemon Modes (Opentrons)
If a run on your robot has failed or paused:
```bash
# Run a single recovery turn to diagnose and propose a fix
labscriptai recover --robot <IP> --run-id <RUN_ID>

# Or run the background daemon to watch the command queue and handle issues automatically
labscriptai daemon --robot <IP> --run-id <RUN_ID>
```

#### Testing Without Hardware (`fake_robot`)
You don't need a physical Opentrons robot to test recovery workflows. You can run the built-in mock server:

```bash
# In terminal 1: start the mock robot server simulating a tip pickup failure
python -m labscriptai.fake_robot --host 127.0.0.1 --port 31950 --scenario tip_missing_budget_block

# In terminal 2: probe the mock robot
labscriptai doctor --robot 127.0.0.1
```

See [`labscriptai/fake_robot/README.md`](labscriptai/fake_robot/README.md) for available mock scenarios (liquid depletion, door open, e-stop, etc.).

To run the package test suite:
```bash
cd labscriptai && pytest -q
```

---

## Repository Structure

```
labscriptai/
  agent/                     # CLI agent implementation (chat, doctor, recover, daemon) and safety gate
  benchmark/logicpass/       # LogicPass / FinalPass_v2 protocol verification engine
  planir/                    # Step plan intermediate representation (Hamilton / Tecan)
  fake_robot/                # Mock Opentrons HTTP server for offline testing
  plugins/skills/            # Recovery playbooks, error taxonomies, and safety briefs
  plugins/mcp/opentrons-mcp/ # Node backend for Opentrons HTTP / WebSocket communication
  webdemo/                   # Interactive browser UI, agent server, and analyze service
  tests/                     # Test suite
assets/                      # Architectural and workflow figures
```

---

## Safety Guidelines for Live Hardware

Before running live protocols on physical equipment, please review the safety specifications:
- [`labscriptai/plugins/skills/safety-brief.md`](labscriptai/plugins/skills/safety-brief.md) — Operational guidelines and boundaries
- [`labscriptai/plugins/skills/error-taxonomy.md`](labscriptai/plugins/skills/error-taxonomy.md) — How errors are detected and classified
- [`labscriptai/plugins/skills/recovery-playbooks.md`](labscriptai/plugins/skills/recovery-playbooks.md) — Pre-approved recovery strategies

*Important:* Never run multiple automated clients or manual scripts against the same robot at the same time.

---

## Cite

Gao, Y. et al. *Autonomous Liquid-handling Robotics Scripting for Accessible and Responsible Protein Engineering.* bioRxiv (2025). [doi:10.1101/2025.09.30.679666, version 2](https://www.biorxiv.org/content/10.1101/2025.09.30.679666v2). The 854-design figure above comes from a newer manuscript draft, not this preprint version.

**Code:** [this repository](https://github.com/KRATSZ/LabScript-AI) · **Study data:** [Zenodo v2, doi:10.5281/zenodo.22054311](https://doi.org/10.5281/zenodo.22054311) (source code is not included in the Zenodo deposit).

## License

MIT
