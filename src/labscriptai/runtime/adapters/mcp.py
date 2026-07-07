"""Runtime adapter for the local Opentrons MCP tool handlers."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..state import RuntimeState

SNAPSHOT_ERROR_KEYS = (
    "robot_status",
    "module_status",
    "parse_error",
    "suggest_recovery_action",
)


@dataclass(frozen=True)
class McpToolConfig:
    index_path: Path = Path("mcp-servers/opentrons-mcp/index.js")
    node_bin: str = "node"
    timeout_sec: float = 30.0


class OpentronsMcpRuntimeAdapter:
    """Small bridge that calls exported MCP tool handlers from Python."""

    def __init__(self, config: McpToolConfig | None = None) -> None:
        self.config = config or McpToolConfig()

    def call_tool(self, tool_name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        env = os.environ.copy()
        env["LABSCRIPTAI_MCP_INDEX"] = str(self.config.index_path.resolve())
        env["LABSCRIPTAI_MCP_TOOL"] = tool_name
        env["LABSCRIPTAI_MCP_ARGS"] = json.dumps(dict(arguments))
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
        completed = subprocess.run(
            [self.config.node_bin, "--input-type=module", "-e", script],
            check=False,
            env=env,
            capture_output=True,
            text=True,
            timeout=self.config.timeout_sec,
        )
        if completed.returncode != 0:
            return {
                "error": "mcp_tool_failed",
                "tool": tool_name,
                "returncode": completed.returncode,
                "stderr": completed.stderr[-4000:],
            }
        try:
            loaded = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            return {"error": "mcp_tool_invalid_json", "tool": tool_name, "stdout": completed.stdout[-4000:]}
        return loaded if isinstance(loaded, dict) else {"data": loaded}

    def recovery_snapshot(self, *, robot_ip: str, run_id: str | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {"robot_ip": robot_ip}
        if run_id:
            args["run_id"] = run_id
        snapshot = {
            "robot_status": self.call_tool("robot_status", args),
            "module_status": self.call_tool("module_status", args),
        }
        if run_id:
            snapshot["parse_error"] = self.call_tool("parse_error", args)
            snapshot["suggest_recovery_action"] = self.call_tool("suggest_recovery_action", args)
        return snapshot

    def execute_suggested_recovery(
        self,
        *,
        robot_ip: str,
        run_id: str,
        suggestion: Mapping[str, Any],
        extra_arguments: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = _unwrap_data(suggestion)
        recovery_branch = payload.get("recovery_branch") or payload.get("action") or payload.get("branch")
        args: dict[str, Any] = {
            "robot_ip": robot_ip,
            "run_id": run_id,
            "recovery_branch": recovery_branch,
        }
        for key in (
            "session_id",
            "recovery_well",
            "tiprack_slot",
            "failed_well",
            "expected_action",
            "timeout_ms",
            "poll_interval_ms",
            "destination_slot",
            "idempotency_key",
        ):
            if key in payload:
                args[key] = payload[key]
        extra = dict(extra_arguments or {})
        for key in ("idempotency_key", "destination_slot", "session_id"):
            if key in extra:
                args[key] = extra[key]
        args.update(extra)
        return self.call_tool("execute_protocol_recovery", args)

    def state_from_snapshot(
        self,
        *,
        robot_ip: str,
        run_id: str,
        snapshot: Mapping[str, Any],
        autonomy_mode: str = "auto",
    ) -> RuntimeState:
        robot_status = _unwrap_data(snapshot.get("robot_status"))
        parse_error = _unwrap_data(snapshot.get("parse_error"))
        status = str(parse_error.get("run_status") or parse_error.get("status") or "recovering")
        phase = "recovering" if "recover" in status or parse_error else "running"
        return RuntimeState(
            run_id=run_id,
            phase=phase,
            robot={
                "host": robot_ip,
                "id": robot_status.get("robot_serial") or robot_status.get("serial"),
                "model": robot_status.get("robot_model") or robot_status.get("model"),
            },
            expected={"autonomy_mode": autonomy_mode, "backend": "opentrons-mcp"},
            observed=dict(snapshot),
        )


def _unwrap_data(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        data = value.get("data")
        if isinstance(data, Mapping):
            return dict(data)
        return dict(value)
    return {}


def snapshot_errors(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for key in SNAPSHOT_ERROR_KEYS:
        payload = snapshot.get(key)
        if not isinstance(payload, Mapping) or not payload.get("error"):
            continue
        detail = dict(payload)
        detail["source"] = key
        errors.append(detail)
    return errors
