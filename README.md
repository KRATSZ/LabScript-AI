# LabscriptAI

**Execution-aware agent framework for liquid-handling laboratory automation**

将自然语言实验意图转化为可验证、可执行、可审计的移液工作站脚本，并在物理运行中支持策略约束下的自恢复。

[![Canonical release](https://img.shields.io/github/v/tag/KRATSZ/LabScript-AI?label=v1.0-canonical)](https://github.com/KRATSZ/LabScript-AI/releases/tag/v1.0-canonical)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.17697326.svg)](https://doi.org/10.5281/zenodo.17697326)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Live web UI:** [labscriptai.cn](https://labscriptai.cn/) — interactive authoring frontend (not the benchmark runner).

---

## Why LabscriptAI

Liquid-handling robots are the workhorses of modern biology: serial dilutions, plate mapping, sample prep, enzyme screens, kit assembly, and foundry-scale distribution. Yet most teams still depend on bespoke scripting—Python APIs, vendor worklists, deck layouts, and simulator quirks—that excludes researchers who think in protocols, not code.

LabscriptAI closes that gap with a **platform-agnostic automation stack**:

- **Authoring** — natural language and SOPs become simulator-validated execution packages through an LLM-driven loop with targeted repair (Precise Refactoring Engine), not wholesale regeneration.
- **Runtime** — instrument state is polled over standard control interfaces; recovery actions pass through a deterministic **Gatekeeper** before any command reaches hardware; successes are logged to trace and case memory for reuse.
- **Cross-vendor scope** — the architecture targets **liquid-handling workstations** broadly (benchtop pipetting robots, integrated deck systems, and biofoundry cells), with concrete adapters and simulators for Opentrons, Hamilton, and Tecan Fluent today and an IR layer designed for extension.
- **Responsible automation** — biosecurity screening, human-in-the-loop checkpoints, and simulation-first gates are first-class, not bolt-ons.

This repository is the **canonical Python implementation** behind the LabscriptAI manuscript benchmark (90-task liquid-handling evaluation, Tables 1–2). It is maintained in sync with the public release branch on [KRATSZ/LabScript-AI](https://github.com/KRATSZ/LabScript-AI/tree/manuscript) (`v1.0-canonical`).

---

## System architecture

Two coupled **deterministic Python control loops** share protocol knowledge, run traces, and recovery case memory:

```
Natural language / SOP
        │
        ▼
┌───────────────────────────────────────┐
│  Authoring loop (LabscriptAgentLoop)  │
│  LLM ↔ ToolRegistry · simulators      │
│  PRE search/replace repair            │
│  → execution package                  │
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│  Runtime loop (RecoveryOrchestrator)  │
│  HTTP/MCP state · error parse         │
│  Gatekeeper approve/block/escalate    │
│  trace.json · case memory             │
└───────────────────────────────────────┘
        │
        ▼
   Liquid-handling workstation
```

| Component | Role |
|-----------|------|
| `LabscriptAgentLoop` | Turn-based authoring: write packages, validate in platform simulators, iterate until pass or retry limit |
| `RecoveryOrchestrator` + `RecoveryQueue` | Poll runs, propose recovery branches, idempotent retries, episodic memory |
| `Gatekeeper` | Deterministic policy on every candidate action before hardware |
| `ToolRegistry` + MCP/HTTP adapters | Pluggable instrument backends; one agent surface, multiple vendors |
| `benchmarks/` + `scripts/` | Reproducible evaluation harness (manuscript Tables 1–2) |

Full design: [`docs/architecture/architecture.md`](docs/architecture/architecture.md) · Agent entry: [`AGENTS.md`](AGENTS.md)

---

## Supported platforms

LabscriptAI is **not** a single-vendor driver. It is built for **liquid-handling workstations** as a class of instrument:

| Class | Examples in tree | Validation path |
|-------|------------------|-----------------|
| Benchtop pipetting robots | Opentrons OT-2, Flex | `opentrons_simulate` |
| High-throughput integrated decks | Hamilton Vantage | PyLabRobot / PyHamilton |
| Biofoundry liquid handlers | Tecan Fluent | pyFluent → worklist compilation |
| Extensible IR | `src/labscriptai/ir/` | Compile/export to vendor targets |

The bundled **833-protocol reference catalog** (`reference-protocols/`) is Opentrons-shaped today—a practical seed library—not a statement that the framework is Opentrons-only. New backends plug in at the adapter and simulator layer without rewriting the agent loops.

---

## Repository layout

| Layer | Paths |
|-------|--------|
| **Python core** | `src/labscriptai/` — agent loop, runtime, benchmark, IR |
| **MCP instrument bridge** | `mcp-servers/opentrons-mcp/` — simulation gate, live control, recovery tools (one concrete backend) |
| **Operator skills** | `skills/*/SKILL.md` — scenario routing for agents and humans |
| **Benchmark tasks** | `benchmarks/` — frozen YAML task suites |
| **Reproducibility** | `docs/reproducibility/` — manuscript runbook, freeze record, Zenodo metadata |
| **Policy & runbooks** | `docs/rules/`, `docs/runbooks/` |
| **Local outputs** | `runs/`, `artifacts/` (gitignored; shard bundle via Zenodo) |

Map: [`docs/REPO_LAYOUT.md`](docs/REPO_LAYOUT.md)

---

## Skills (operator routing)

| Skill | When to use |
|-------|-------------|
| `opentrons-experiment-run` | Default live execution, status, resume, recovery |
| `opentrons-experiment-intent-review` | Plate mapping, tip strategy, deck alignment before authoring |
| `opentrons-protocol-author` | Write or revise Python protocols |
| `opentrons-protocol-verify` | Local doctor / analyze / simulate (no MCP) |
| `opentrons-simulation-repair` | Simulate → parse → edit loop |
| `opentrons-protocol-library` | Search the 833-protocol catalog |
| `opentrons-robot-lan` | HTTP route when MCP unavailable or for debug |

Skill folder names retain historical `opentrons-*` prefixes; behavior is defined by [`docs/rules/workflows.md`](docs/rules/workflows.md) and extends to additional liquid-handler backends as adapters land.

---

## Quick start

```bash
git clone https://github.com/KRATSZ/LabScript-AI.git
cd LabScript-AI
git checkout v1.0-canonical

uv venv .venv && uv sync
cd mcp-servers/opentrons-mcp && npm install && cd ../..

# Tests
uv run pytest
cd mcp-servers/opentrons-mcp && npm test
```

**Reproduce manuscript Tables 1–2 without LLM calls** (requires Zenodo `runs/` shard bundle):

```bash
PYTHONPATH=src uv run python scripts/build_table1_v2.py
```

Step-by-step: [`docs/reproducibility/manuscript_canonical_runbook.md`](docs/reproducibility/manuscript_canonical_runbook.md)

### Development clone (this workspace)

```bash
git clone https://github.com/SmartisanNaive/Opentrons-Lab-Agent.git
cd Opentrons-Lab-Agent
uv venv .venv && uv sync
```

---

## Example commands

```bash
# Local runtime smoke (no robot API)
PYTHONPATH=src uv run python -m labscriptai.runtime.smoke_benchmark \
  --provider offline --output-dir runs/runtime-smoke/offline-demo

# Small authoring pilot with simulation
PYTHONPATH=src uv run python -m labscriptai.benchmark.authoring_pilot \
  --provider offline --simulate --limit 3 \
  --output-dir runs/authoring-pilot/offline-sim-demo

# Search reference protocols
uv run python skills/opentrons-protocol-library/scripts/search_protocols.py search "serial dilution"
```

Live runs require instrument connectivity, API keys for LLM providers, and adherence to [`docs/rules/safety-policy.md`](docs/rules/safety-policy.md).

---

## Documentation

| Document | Role |
|----------|------|
| [`docs/README.md`](docs/README.md) | Doc map and priority |
| [`docs/rules/workflows.md`](docs/rules/workflows.md) | End-to-end tool order |
| [`docs/rules/safety-policy.md`](docs/rules/safety-policy.md) | Hard bans, deck truth, vision tiering |
| [`docs/rules/error-response.md`](docs/rules/error-response.md) | Error taxonomy and recovery |
| [`docs/reproducibility/`](docs/reproducibility/) | Manuscript reproduction |
| [`docs/architecture/architecture.md`](docs/architecture/architecture.md) | Layer diagram (text) |

---

## Citation & data

- **Code (canonical):** [github.com/KRATSZ/LabScript-AI/tree/v1.0-canonical](https://github.com/KRATSZ/LabScript-AI/tree/v1.0-canonical) — branch `manuscript`, tag `v1.0-canonical`
- **Data & benchmark shards:** [Zenodo 10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)
- **Web interface:** [labscriptai.cn](https://labscriptai.cn/)
- **Citation metadata:** `CITATION.cff` (at canonical release)

Manuscript source (working draft): `docs/paper/.laipaper/main0714.md` (supersedes removed `.paper/main0706.md`).

---

## Using as a dependency

### Git submodule

```bash
git submodule add https://github.com/KRATSZ/LabScript-AI.git labscriptai
cd labscriptai && git checkout v1.0-canonical
```

### MCP server only

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/path/to/mcp-servers/opentrons-mcp/index.js"]
    }
  }
}
```

---

## License

MIT
