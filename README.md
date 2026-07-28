# LabscriptAI

**Execution-aware agent for liquid-handling laboratory automation**

Natural-language lab intent → verifiable Opentrons scripts, with policy-constrained recovery on live Flex.

[![Canonical release](https://img.shields.io/github/v/tag/KRATSZ/LabScript-AI?label=v1.0-canonical)](https://github.com/KRATSZ/LabScript-AI/releases/tag/v1.0-canonical)
[![Zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.17697326.svg)](https://doi.org/10.5281/zenodo.17697326)

**Live web UI:** [labscriptai.cn](https://labscriptai.cn/)

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

# robot act/status needs Node deps once:
(cd plugins/mcp/opentrons-mcp && npm install)

labscriptai doctor --robot <ROBOT_IP>
labscriptai chat --robot <ROBOT_IP>   # default provider: deepseek (DEEPSEEK_API_KEY)
# offline smoke only: labscriptai chat --provider offline
pytest -q
```

Copy env vars into a `.env` file in the repo root (or export them), for example:

```
DEEPSEEK_API_KEY=your_key_here
ROBOT_IP=192.168.x.x
```

Optional: `ARK_API_KEY` (MCP vision), `LABSCRIPTAI_WORKSPACE` (default workspace for `edit`; falls back to cwd), `LABSCRIPTAI_MCP_INDEX` (MCP server override).

Do **not** install a local `core/` tree into the same venv (both claim the `labscriptai` console script).

---

## Layout

```
labscriptai/                 # pip install -e .  ← only package entry
  agent/                     # llm, gate, tools, loop, cli
  plugins/
    skills/*.md              # on-demand via `skill` tool
    mcp/opentrons-mcp/       # vendored Node MCP (npm install locally)
  tests/
  pyproject.toml
```

| Piece | Location |
|-------|----------|
| CLI (`doctor` / `chat`) | `labscriptai/agent/` |
| Skills | `labscriptai/plugins/skills/*.md` |
| Vendored MCP | `labscriptai/plugins/mcp/opentrons-mcp/` |
| Package tests | `labscriptai/tests/` |

Packaging: skills + MCP sources ship in the wheel; `node_modules/` is gitignored — run `npm install` after clone. Paths resolve from the installed package, not a developer absolute path.

---

## Safety (live Flex)

Load on demand via the `skill` tool, or read:

- [`labscriptai/plugins/skills/safety-brief.md`](labscriptai/plugins/skills/safety-brief.md)
- [`labscriptai/plugins/skills/error-taxonomy.md`](labscriptai/plugins/skills/error-taxonomy.md)
- [`labscriptai/plugins/skills/recovery-playbooks.md`](labscriptai/plugins/skills/recovery-playbooks.md)

Hard stops (`HARDWARE_FAULT`, `DECK_COLLISION`, `UNKNOWN`) always escalate to a human. Prefer MCP for live control; never run MCP and HTTP control against the same robot in parallel.

---

## MCP (Cursor / IDE)

Root [`.mcp.json`](.mcp.json) already points at the vendored server:

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

## What this branch is (and is not)

This `manuscript` tree is the **runnable 5-tool CLI agent** for colleagues and live Flex. Evaluation / paper-reproduction code is **not** on this branch (archived on [Zenodo](https://doi.org/10.5281/zenodo.17697326)). Local leftovers (`benchmarks/`, `src/`, `docs/`, `core/`, …) stay gitignored if present on disk.

---

## Citation

- **Code:** [github.com/KRATSZ/LabScript-AI](https://github.com/KRATSZ/LabScript-AI/tree/manuscript) — branch `manuscript`
- **Benchmark / shard data:** [Zenodo 10.5281/zenodo.17697326](https://doi.org/10.5281/zenodo.17697326)

## License

MIT
