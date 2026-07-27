# LabscriptAI

Live entrypoint: **`labscriptai/`** (5-tool CLI: `bash`, `edit`, `robot`, `memory`, `skill`).

```bash
cd labscriptai
pip install -e .
(cd plugins/mcp/opentrons-mcp && npm install)
labscriptai doctor --robot <ROBOT_IP>
labscriptai chat --provider offline
```

Details: [`README.md`](README.md). Safety / recovery: `labscriptai/plugins/skills/` (`safety-brief`, `error-taxonomy`, `recovery-playbooks`). MCP: [`.mcp.json`](.mcp.json) → `labscriptai/plugins/mcp/opentrons-mcp/`.
