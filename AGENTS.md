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

Fake Flex HTTP backend (reproduce tip/liquid recovery failures without a robot): `python -m labscriptai.fake_robot --scenario tip_missing_budget_block` then `labscriptai doctor --robot 127.0.0.1`. See [`labscriptai/fake_robot/README.md`](labscriptai/fake_robot/README.md).
