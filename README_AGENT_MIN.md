# LabscriptAI lean agent (minimal)

Standalone package under `labscriptai/` — five tools (`bash`, `edit`, `robot`, `memory`, `skill`), gate allow/ask/suspend, vendored MCP under `plugins/`.

This does **not** replace `core/` or `src/labscriptai`. Install **only** this tree for the colleague CLI.

## Install (colleagues)

Use a **fresh venv** (do not combine with `core/` — both register the `labscriptai` console script):

```bash
cd labscriptai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
# optional tests:
pip install -e ".[dev]"

# robot act/status needs Node deps once:
(cd plugins/mcp/opentrons-mcp && npm install)
```

Then:

```bash
labscriptai doctor --robot <ROBOT_IP>          # probes http://<IP>:31950/health
labscriptai chat --provider offline            # no API key
labscriptai chat --provider deepseek --robot <ROBOT_IP>
pytest -q
```

Env: `DEEPSEEK_API_KEY` (optional). Workspace for `edit`: `LABSCRIPTAI_WORKSPACE` or cwd. MCP override: `LABSCRIPTAI_MCP_INDEX`.

## Layout

```
labscriptai/
  __init__.py
  agent/           # llm, gate, tools, loop, cli, mcp_adapter
  plugins/
    skills/*.md    # on-demand via `skill` tool
    mcp/opentrons-mcp/   # vendored Node MCP (npm install locally)
  tests/
  pyproject.toml
```

## Packaging notes

- `package-data` includes `plugins/skills/*.md` and MCP sources (`index.js`, `lib/`, …).
- `node_modules/` is gitignored and excluded from sdist/wheel — run `npm install` after clone.
- Skills/MCP paths resolve relative to the installed package (`Path(__file__).parents[1]/plugins/...`), not a developer absolute path.

## Conflict with `core/`

| Tree | Dist name | Script | Use |
|------|-----------|--------|-----|
| `labscriptai/` (this) | `labscriptai` | `labscriptai` → `agent.cli:main` | Colleague live/chat/doctor |
| `core/` | `labscriptai` | `labscriptai` → `labscriptai.cli:main` | Older monorepo core |
| `src/labscriptai/` | via root `opentrons-lab-agent` | (no colliding script) | Manuscript / benchmarks |

**Rule:** `cd labscriptai && pip install -e .` in an isolated venv. Do not `pip install -e core` into the same environment.

## Quick checks

```bash
labscriptai doctor --robot 127.0.0.1
printf '/quit\n' | labscriptai chat --provider offline
```

Live Flex caveat: doctor/chat need a reachable robot on `:31950`. Connection refused / closed is an environment issue, not an agent crash.
