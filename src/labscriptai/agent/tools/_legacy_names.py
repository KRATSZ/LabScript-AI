"""Model-exposed legacy names mapped to the ten unified tool names."""

from __future__ import annotations

import json
from typing import Any, Mapping

from labscriptai.agent.tools import TOOL_NAMES, ToolCall, ToolName

LEGACY_TOOL_NAMES: dict[str, tuple[ToolName, dict[str, Any]]] = {
    "read_file": ("package.read_write", {"op": "read"}),
    "write_file": ("package.read_write", {"op": "write"}),
    "apply_patch": ("package.patch", {}),
    "str_replace": ("package.read_write", {"op": "str_replace"}),
    "json_set": ("package.read_write", {"op": "json_set"}),
    "append_md": ("package.read_write", {"op": "append_md"}),
    "validate_package": ("package.validate", {}),
    "run_simulate": ("package.simulate", {}),
    "load_skill": ("skill.search_load", {"op": "load"}),
    "search_protocol_library": ("protocol.search", {}),
    "robot_inspect": ("robot.inspect", {}),
    "error_parse": ("error.parse", {}),
    "recovery_suggest": ("recovery.suggest", {}),
    "run_control": ("run.control", {}),
    "package_read_write": ("package.read_write", {}),
    "package_patch": ("package.patch", {}),
    "package_validate": ("package.validate", {}),
    "package_simulate": ("package.simulate", {}),
    "skill_search_load": ("skill.search_load", {}),
    "memory_read_write": ("memory.read_write", {}),
    "protocol_search": ("protocol.search", {}),
    "shell_run": ("shell.run", {}),
}


def normalize_tool_call(raw: Mapping[str, Any] | ToolCall) -> ToolCall:
    if isinstance(raw, ToolCall):
        return raw
    name = str(raw.get("name") or raw.get("function", {}).get("name") or "")
    arguments = raw.get("arguments")
    if arguments is None and isinstance(raw.get("function"), Mapping):
        arguments = raw["function"].get("arguments")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}
    args = dict(arguments) if isinstance(arguments, Mapping) else {}
    reason = str(raw.get("reason") or args.get("reason") or args.get("why") or "")
    call_id = raw.get("id") or raw.get("call_id")
    if name in LEGACY_TOOL_NAMES:
        tool_name, injected = LEGACY_TOOL_NAMES[name]
        return ToolCall(
            name=tool_name,
            arguments={**injected, **args},
            reason=reason,
            call_id=str(call_id) if call_id else None,
        )
    if name in TOOL_NAMES:
        return ToolCall(
            name=name,  # type: ignore[arg-type]
            arguments=args,
            reason=reason,
            call_id=str(call_id) if call_id else None,
        )
    return ToolCall(
        name="package.read_write",
        arguments={"op": "__unknown__", "raw_name": name, **args},
        reason=reason,
        call_id=str(call_id) if call_id else None,
    )
