"""Short-lived Node subprocess bridge to vendored Opentrons MCP TOOL_HANDLERS.

Copied pattern from core/labscriptai/runtime/adapters/mcp.py::call_tool —
no MCP Client SDK on the Python side.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

DEFAULT_ROBOT_PORT = 31950
WATCH_TIMEOUT_SEC = 90.0
DEFAULT_TIMEOUT_SEC = 30.0
RUN_PROTOCOL_TIMEOUT_SEC = 600.0


def plugins_mcp_index() -> Path:
    """Default vendored MCP entry (override with LABSCRIPTAI_MCP_INDEX)."""
    env = os.environ.get("LABSCRIPTAI_MCP_INDEX")
    if env:
        return Path(env).resolve()
    return (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "mcp"
        / "opentrons-mcp"
        / "index.js"
    ).resolve()


def normalize_robot_base(host: str | None) -> str:
    """Normalize robot host to ``http://host:31950``.

    Respects an existing scheme or ``host:port`` form (mirrors
    ``core/mcp/opentrons-mcp/lib/http.js`` ``normalizeBaseUrl``).
    """
    if host is None or not str(host).strip():
        raise ValueError("robot host is required")
    raw = str(host).strip().rstrip("/")
    if re.match(r"^https?://", raw, re.I):
        return raw
    if re.match(r"^[^/]+:\d+$", raw):
        return f"http://{raw}"
    return f"http://{raw}:{DEFAULT_ROBOT_PORT}"


def call_tool(
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    index_path: Path | None = None,
    node_bin: str = "node",
    timeout_sec: float | None = None,
) -> dict[str, Any]:
    """Invoke one MCP TOOL_HANDLERS entry via a short-lived Node subprocess."""
    index = (index_path or plugins_mcp_index()).resolve()
    if not index.is_file():
        return {
            "error": "mcp_index_missing",
            "tool": tool_name,
            "index_path": str(index),
        }

    env = os.environ.copy()
    env["LABSCRIPTAI_MCP_INDEX"] = str(index)
    env["LABSCRIPTAI_MCP_TOOL"] = tool_name
    env["LABSCRIPTAI_MCP_ARGS"] = json.dumps(dict(arguments or {}))
    script = """
const { pathToFileURL } = await import("node:url");
const indexPath = process.env.LABSCRIPTAI_MCP_INDEX;
const toolName = process.env.LABSCRIPTAI_MCP_TOOL;
const args = JSON.parse(process.env.LABSCRIPTAI_MCP_ARGS || "{}");
const mod = await import(pathToFileURL(indexPath).href);
const handler = mod.TOOL_HANDLERS?.[toolName];
if (!handler) {
  throw new Error(`Unknown MCP tool: ${toolName}`);
}
const result = await handler(args);
process.stdout.write(JSON.stringify(result ?? {}));
"""
    limit = float(timeout_sec if timeout_sec is not None else DEFAULT_TIMEOUT_SEC)
    try:
        completed = subprocess.run(
            [node_bin, "--input-type=module", "-e", script],
            check=False,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=limit,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "error": "mcp_tool_timeout",
            "tool": tool_name,
            "timeout_sec": limit,
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
        }
    except OSError as exc:
        return {
            "error": "mcp_tool_spawn_failed",
            "tool": tool_name,
            "detail": str(exc),
        }

    if completed.returncode != 0:
        return {
            "error": "mcp_tool_failed",
            "tool": tool_name,
            "returncode": completed.returncode,
            "stderr": (completed.stderr or "")[-4000:],
        }
    try:
        loaded = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "error": "mcp_tool_invalid_json",
            "tool": tool_name,
            "stdout": (completed.stdout or "")[-4000:],
        }
    return loaded if isinstance(loaded, dict) else {"data": loaded}
