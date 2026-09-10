# LabscriptAI

**This branch (`pi-agent`):** [local chat demo](labscriptai/webdemo/README.md) — OT-2 / Flex, 8010 Python, Watch after FinalPass_v2; no live Flex.

**Paper CLI (`manuscript`):** `labscriptai chat` below.

**Execution-aware agent for liquid-handling laboratory automation**

Natural-language lab intent → verifiable Opentrons scripts, with policy-constrained recovery on live Flex.

[![Canonical release](https://img.shields.io/github/v/tag/KRATSZ/LabScript-AI?label=v1.0-canonical)](https://github.com/KRATSZ/LabScript-AI/releases/tag/v1.0-canonical)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.17697326.svg)](https://doi.org/10.5281/zenodo.17697326)

**Live web UI:** [labscriptai.cn](https://labscriptai.cn/)

The only documented user entry is **`labscriptai chat`**. `labscriptai doctor` is a health check so a colleague can get chat working — not a second workflow.

---

## Install

The only installable package on this branch is **`labscriptai/`** (5-tool loop: `bash`, `edit`, `robot`, `memory`, `skill`). Use a **fresh venv**:

```bash
git clone https://github.com/KRATSZ/LabScript-AI.git
cd LabScript-AI
git checkout manuscript

cd labscriptai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
# optional tests:
pip install -e ".[dev]"

cd plugins/mcp/opentrons-mcp && npm install && cd -

labscriptai doctor --robot <ROBOT_IP>
labscriptai chat                  # default provider: deepseek (DEEPSEEK_API_KEY)
# offline smoke only: labscriptai chat --provider offline
pytest -q
```

`--robot` is optional on `doctor`: toolchain checks (Node ≥ 18, `node_modules`, `index.js`, `DEEPSEEK_API_KEY`, Opentrons imports) always run. Pass `--robot` only to probe `http://IP:31950/health`.

Copy env vars into a `.env` file in the repo root (or export them), for example:

```
DEEPSEEK_API_KEY=your_key_here
ROBOT_IP=192.168.x.x
```

Optional: `LABSCRIPTAI_WORKSPACE` (default workspace for `edit`; falls back to cwd), `LABSCRIPTAI_MCP_INDEX` (override path to the robot backend `index.js`).

MCP `index.js` is the **robot backend** for chat (`mcp_adapter.call_tool` — short-lived Node import of `TOOL_HANDLERS`). It is not a Cursor plugin and not a second tool surface.

Do **not** install a local `core/` tree into the same venv (both claim the `labscriptai` console script).

---

## Layout

```
labscriptai/                 # pip install -e .  ← only package entry
  agent/                     # llm, gate, tools, loop, cli
  benchmark/logicpass/       # runtime LogicPass / FinalPass_v2 engine
  plugins/
    skills/*.md              # on-demand via `skill` tool
    mcp/opentrons-mcp/       # Node robot backend (npm install locally)
  tests/
  pyproject.toml
```

| Piece | Location |
|-------|----------|
| CLI (`chat`; `doctor` health check) | `labscriptai/agent/` |
| Runtime LogicPass / FinalPass_v2 | `labscriptai/benchmark/logicpass/` |
| Skills | `labscriptai/plugins/skills/*.md` |
| Robot backend (Node) | `labscriptai/plugins/mcp/opentrons-mcp/` |
| Protocol examples | `labscriptai/plugins/mcp/opentrons-mcp/examples/` |
| Package tests | `labscriptai/tests/` |

Packaging: skills + MCP sources ship in the wheel; `node_modules/` is gitignored — run `npm install` after clone. Paths resolve from the installed package, not a developer absolute path.

---

## Safety (live Flex)

Load on demand via the `skill` tool, or read:

- [`labscriptai/plugins/skills/safety-brief.md`](labscriptai/plugins/skills/safety-brief.md)
- [`labscriptai/plugins/skills/error-taxonomy.md`](labscriptai/plugins/skills/error-taxonomy.md)
- [`labscriptai/plugins/skills/recovery-playbooks.md`](labscriptai/plugins/skills/recovery-playbooks.md)

Hard stops (`HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN`) always escalate to a human. Live robot actions go through the chat `robot` tool (Node MCP backend); never run a second HTTP control path against the same robot in parallel.

---

## What this branch is (and is not)

This `manuscript` tree is the **runnable 5-tool CLI agent** for colleagues and live Flex. The runtime LogicPass / FinalPass_v2 engine is included because the product loop depends on it. The 90-question evaluation harness and reports, paper drafts, Commec/iGEM data, run histories, and binary archives are external research materials.

---

## Citation

- **Code:** [github.com/KRATSZ/LabScript-AI](https://github.com/KRATSZ/LabScript-AI/tree/manuscript) — branch `manuscript`
- **Benchmark / shard data:** [Zenodo 10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)

## License

MIT
