# Opentrons robot backend

Node backend for **`labscriptai chat`** (`mcp_adapter.call_tool` → `TOOL_HANDLERS` in `index.js`). Not a Cursor plugin and not a second CLI.

```bash
cd labscriptai/plugins/mcp/opentrons-mcp && npm install
```

User entry and health check: repo-root [`README.md`](../../../../README.md). Safety / recovery: [`../skills/`](../../skills/) (`safety-brief`, `error-taxonomy`, `recovery-playbooks`, `pressure-trace`).

Override the entry with `LABSCRIPTAI_MCP_INDEX=/abs/path/to/index.js` if needed. Live pressure sampling is opt-in (`OPENTRONS_ENABLE_PRESSURE_TRACE=1`) and never authorizes play/resume.

Pressure evidence is advisory and cannot override controller state. Tools: `run_pressure_trace`, `fetch_pressure_trace`, `analyze_pressure_trace`.

| Feature / tool | Status | Notes |
|---|---|---|
| `run_pressure_trace` | stable | Generate hover/z_trace/during_probe protocol; `execute_on_robot` opt-in |
| `fetch_pressure_trace` | stable | Pull PRESSURE_CSV_B64 comments from a finished run |
| `analyze_pressure_trace` | stable | Feature extraction; observation-only |
