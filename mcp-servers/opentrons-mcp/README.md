# Opentrons Lab MCP

This folder contains a practical MCP server for `Opentrons-Lab-Agent`.

It is intentionally focused on the highest-value workflow for Claude Code:

- a few useful live robot control tools
- local `opentrons.simulate` integration
- structured simulation parsing for multi-round protocol repair

## Why this server exists

The repository already includes Python-first skills for:

- writing protocols
- verifying protocols locally
- controlling a robot over LAN

This MCP server adds a tighter tool loop for agent orchestration:

1. `doctor_local_runtime`
2. `simulate_protocol`
3. `parse_simulation_output`
4. edit protocol
5. retry until pass

It also exposes a compact set of live tools:

- `robot_health`
- `get_protocols`
- `upload_protocol`
- `create_run`
- `control_run`
- `get_runs`
- `get_run_status`

## Notes

- The tool surface is inspired by the community project `yerbymatey/opentrons-mcp`, but reduced to the parts that are most useful for this repository's simulation-first workflow.
- For API documentation lookup, pair this server with `opentrons-document-mcp-server`.

## Install

```bash
cd mcp-servers/opentrons-mcp
npm install
```

## Test

```bash
npm test
```

## Example MCP config

```json
{
  "mcpServers": {
    "opentrons-lab": {
      "command": "node",
      "args": ["/ABSOLUTE/PATH/TO/Opentrons-Lab-Agent/mcp-servers/opentrons-mcp/index.js"]
    },
    "opentrons-docs": {
      "command": "npx",
      "args": ["-y", "opentrons-document-mcp-server@latest"]
    }
  }
}
```

If your simulation environment is not on the default `python3`, either:

- set `OPENTRONS_PYTHON`, or
- pass `python_executable` to the simulation tools.
