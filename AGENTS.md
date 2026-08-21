# LabscriptAI

Live entrypoint: **`labscriptai chat`** (5-tool CLI: `bash`, `edit`, `robot`, `memory`, `skill`). `labscriptai doctor` is a health check, not a second workflow.

MCP `index.js` is the robot backend for chat (`mcp_adapter.call_tool`), not a Cursor plugin and not a second tool surface.

```bash
cd labscriptai
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cd plugins/mcp/opentrons-mcp && npm install && cd -
labscriptai doctor --robot <ROBOT_IP>
labscriptai chat                  # default provider: deepseek (DEEPSEEK_API_KEY)
```

`--robot` is optional on `doctor` (toolchain always; `/health` only with `--robot`). Details: [`README.md`](README.md). Safety / recovery: `labscriptai/plugins/skills/` (`safety-brief`, `error-taxonomy`, `recovery-playbooks`).
