# LabscriptAI

**Execution-aware agent for liquid-handling laboratory automation**

将自然语言实验意图转化为可验证、可执行的移液工作站脚本，并在物理运行中支持策略约束下的恢复。

[![Canonical release](https://img.shields.io/github/v/tag/KRATSZ/LabScript-AI?label=v1.0-canonical)](https://github.com/KRATSZ/LabScript-AI/releases/tag/v1.0-canonical)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.17697326.svg)](https://doi.org/10.5281/zenodo.17697326)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Live web UI:** [labscriptai.cn](https://labscriptai.cn/)

---

## Install (colleagues — start here)

The installable entrypoint is the lean package under **`labscriptai/`** (5-tool loop: `bash`, `edit`, `robot`, `memory`, `skill`). Use a **fresh venv**:

```bash
git clone https://github.com/KRATSZ/LabScript-AI.git
cd LabScript-AI
git checkout manuscript

cd labscriptai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
# robot act/status needs Node deps once:
(cd plugins/mcp/opentrons-mcp && npm install)

labscriptai doctor --robot <ROBOT_IP>
labscriptai chat --provider offline
# or: labscriptai chat --provider deepseek --robot <ROBOT_IP>
```

Details: [`README_AGENT_MIN.md`](README_AGENT_MIN.md). Env: `DEEPSEEK_API_KEY` (optional). MCP override: `LABSCRIPTAI_MCP_INDEX`.

Do **not** install local `core/` into the same venv (both claim the `labscriptai` console script).

---

## What this branch ships

| Path | Role |
|------|------|
| **`labscriptai/`** | Lean CLI agent + vendored MCP under `plugins/mcp/` + skills under `plugins/skills/` |
| `src/labscriptai/` | Historical runtime / IR baseline (not required for colleague CLI install) |
| `docs/` | Rules, architecture, reproducibility notes |
| Root meta | `README.md`, `README_AGENT_MIN.md`, `AGENTS.md`, `CITATION.cff`, `.env.example` |

**Removed from this branch (not needed to run CLI or live Flex):** evaluation corpora under `benchmarks/`, the 833-protocol `reference-protocols/` tree, duplicate root `mcp-servers/`, root `skills/` / `scripts/` / `tests/` / `schemas/`, `vision/`, and `supplementary/`. Local leftovers stay gitignored so they are not re-added by mistake. Manuscript evaluation shards remain on [Zenodo](https://doi.org/10.5281/zenodo.17697326).

---

## Repository layout (lean)

```
labscriptai/           # pip install -e .  ← colleague entry
  agent/               # llm, gate, tools, loop, cli
  plugins/
    skills/*.md
    mcp/opentrons-mcp/ # vendored Node MCP (npm install locally)
  tests/
src/labscriptai/       # retained baseline library
docs/rules/            # safety / workflows / error-response
```

Agent entry for operators: [`AGENTS.md`](AGENTS.md) → points at `labscriptai/`.

---

## MCP (Cursor / IDE)

Vendored server path (after clone):

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["labscriptai/plugins/mcp/opentrons-mcp/index.js"]
    }
  }
}
```

---

## Documentation

| Document | Role |
|----------|------|
| [`README_AGENT_MIN.md`](README_AGENT_MIN.md) | Lean agent install & layout |
| [`docs/rules/safety-policy.md`](docs/rules/safety-policy.md) | Hard bans, deck truth |
| [`docs/rules/workflows.md`](docs/rules/workflows.md) | Tool order |
| [`docs/rules/error-response.md`](docs/rules/error-response.md) | Error taxonomy / recovery |
| [`docs/architecture/architecture.md`](docs/architecture/architecture.md) | Layer overview |
| [`docs/reproducibility/`](docs/reproducibility/) | Manuscript / Zenodo notes |

---

## Citation & data

- **Code:** [github.com/KRATSZ/LabScript-AI](https://github.com/KRATSZ/LabScript-AI/tree/manuscript) — branch `manuscript`
- **Benchmark / shard data (archived):** [Zenodo 10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)
- **Citation metadata:** `CITATION.cff`

---

## License

MIT
