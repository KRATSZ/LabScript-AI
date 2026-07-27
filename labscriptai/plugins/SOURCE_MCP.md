# MCP vendor source

| Field | Value |
|-------|--------|
| Package | `labscriptai/plugins/mcp/opentrons-mcp/` |
| Copied from | `core/mcp/opentrons-mcp/` (primary) |
| Fallbacks (if primary missing) | `mcp-servers/opentrons-mcp/`, `../labscriptai-ot/servers/opentrons-mcp/` |
| Default HTTP port | `31950` (`lib/http.js` `DEFAULT_PORT`) |
| Entry | `index.js` (`TOOL_HANDLERS` export) |
| Excluded from vendor | `node_modules/`, `test/`, logs, `runs/` |

## Local install

```bash
cd labscriptai/plugins/mcp/opentrons-mcp
npm install
```

Override path with `LABSCRIPTAI_MCP_INDEX=/abs/path/to/index.js`.

## Call path

Python `labscriptai.agent.mcp_adapter.call_tool` spawns a short-lived `node --input-type=module -e …` process that `import()`s `index.js` and invokes `TOOL_HANDLERS[name](args)`. No MCP Client SDK on the Python side.
