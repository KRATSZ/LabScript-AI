"""Lean agent tools: bash, edit, robot, memory, skill.

``execute`` runs tools already allowed by the outer gate — no gating here.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .gate import (
    RESUME_BLOCKED_RUN_STATUSES,
    coerce_path_into_workspace,
    resolve_robot_act_label,
)
from .mcp_adapter import (
    RUN_PROTOCOL_TIMEOUT_SEC,
    WATCH_TIMEOUT_SEC,
    call_tool,
    normalize_robot_base,
    plugins_mcp_index,
)

__all__ = (
    "TOOLS_SCHEMA",
    "execute",
    "normalize_robot_base",
    "plugins_mcp_index",
)

_MEMORY_DIRNAME = ".labscriptai/memory"


def _default_opentrons_python() -> str | None:
    """Prefer labscriptai/.venv python that has opentrons installed."""
    env = (os.environ.get("OPENTRONS_PYTHON") or "").strip()
    if env and Path(env).is_file():
        return env
    # tools.py → labscriptai/agent → labscriptai → repo
    here = Path(__file__).resolve()
    package_root = here.parents[1]  # labscriptai/
    candidates = [
        package_root / ".venv" / "Scripts" / "python.exe",
        package_root / ".venv" / "bin" / "python",
        package_root.parent / ".venv" / "Scripts" / "python.exe",
        package_root.parent / ".venv" / "bin" / "python",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def _ensure_python_executable(payload: dict[str, Any]) -> None:
    if payload.get("python_executable"):
        return
    resolved = _default_opentrons_python()
    if resolved:
        payload["python_executable"] = resolved


def _resolve_bash_output_limit() -> int:
    """Chars kept from bash stdout/stderr; 0 = no truncation."""
    raw = os.environ.get("LABSCRIPTAI_MAX_BASH_OUTPUT", "0")
    try:
        return max(0, int(str(raw).strip()))
    except ValueError:
        return 0


_MAX_BASH_OUTPUT = _resolve_bash_output_limit()


def _skills_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "plugins" / "skills"


TOOLS_SCHEMA: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the workspace (cwd=workspace). Gate runs outside this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command string executed via bash -lc.",
                    },
                    "timeout_sec": {
                        "type": "number",
                        "description": "Timeout seconds (default 30).",
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit",
            "description": "Read, write, or str_replace a file under the workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": ["read", "write", "str_replace"],
                    },
                    "path": {
                        "type": "string",
                        "description": "Workspace-relative path.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content for write.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "Exact substring to replace (str_replace).",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "Replacement text (str_replace).",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default false).",
                    },
                },
                "required": ["op", "path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "robot",
            "description": (
                "Robot ops via short-lived MCP TOOL_HANDLERS. "
                "op=status|watch|act. act action_type includes simulate_protocol, "
                "run_pressure_trace, analyze_pressure_trace (advisory; execute_on_robot not true by default). "
                "parse_error/suggest_recovery embed under status when run_id is set."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": ["status", "watch", "act"],
                    },
                    "run_id": {"type": "string"},
                    "session_id": {"type": "string"},
                    "include_modules": {
                        "type": "boolean",
                        "description": "status: also call module_status (default true).",
                    },
                    "prefer_outbox": {
                        "type": "boolean",
                        "description": "watch: try runtime_get_outbox before watch_poll (default false).",
                    },
                    "recovery_branch": {
                        "type": "string",
                        "description": "act: execute_protocol_recovery branch (or pass under args).",
                    },
                    "action": {
                        "type": "string",
                        "description": "act: explicit MCP control tool name when not using recovery.",
                    },
                    "action_type": {
                        "type": "string",
                        "description": "act: gate/action label (alias; may mirror recovery_branch or control name).",
                    },
                    "args": {
                        "type": "object",
                        "description": "Extra MCP arguments (passthrough for act/watch).",
                    },
                },
                "required": ["op"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": "Read/write/search markdown notes under workspace/.labscriptai/memory/.",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": ["read", "write", "list", "search"],
                    },
                    "name": {
                        "type": "string",
                        "description": "Note stem or filename (e.g. note.md or note).",
                    },
                    "content": {
                        "type": "string",
                        "description": "Markdown body for write.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Substring search query.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max search hits (default 10).",
                    },
                },
                "required": ["op"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skill",
            "description": "Load a skill markdown from plugins/skills/{name}.md; empty name lists skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill stem without .md; omit or empty to list.",
                    },
                },
            },
        },
    },
]


def execute(
    name: str,
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    """Execute a gate-allowed tool; return a JSON-able dict."""
    args = dict(args or {})
    workspace = Path(workspace).resolve()
    session = dict(session or {})
    handlers = {
        "bash": _bash,
        "edit": _edit,
        "robot": _robot,
        "memory": _memory,
        "skill": _skill,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": "unknown_tool", "name": name, "allowed": sorted(handlers)}
    try:
        return handler(args, workspace=workspace, robot_ip=robot_ip, session=session)
    except Exception as exc:  # noqa: BLE001 — tools must never crash the loop
        return {"error": "tool_exception", "tool": name, "detail": str(exc)}


# --- bash ------------------------------------------------------------------


def _bash(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    del robot_ip, session
    command = args.get("command")
    if not isinstance(command, str) or not command.strip():
        return {"error": "invalid_args", "detail": "command must be a non-empty string"}
    timeout = float(args.get("timeout_sec") or 30)
    timeout = max(1.0, min(timeout, 600.0))
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "error": "timeout",
            "command": command,
            "timeout_sec": timeout,
            "stdout": _clip(exc.stdout or ""),
            "stderr": _clip(exc.stderr or ""),
            "rc": None,
        }
    return {
        "stdout": _clip(completed.stdout or ""),
        "stderr": _clip(completed.stderr or ""),
        "rc": completed.returncode,
    }


def _clip(text: str, limit: int | None = None) -> str:
    cap = _MAX_BASH_OUTPUT if limit is None else limit
    if cap <= 0 or len(text) <= cap:
        return text
    return text[:cap] + f"\n…[truncated {len(text) - cap} chars]"


# --- edit ------------------------------------------------------------------


def _edit(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    del robot_ip, session
    op = str(args.get("op") or "")
    rel = args.get("path")
    if not isinstance(rel, str) or not rel.strip():
        return {"error": "invalid_args", "detail": "path is required"}
    rel = coerce_path_into_workspace(rel, workspace)
    args["path"] = rel
    try:
        path = _resolve_under(workspace, rel)
    except ValueError as exc:
        return {"error": "path_escape", "detail": str(exc)}

    if op == "read":
        if not path.is_file():
            return {"error": "not_found", "path": _rel(workspace, path)}
        return {"path": _rel(workspace, path), "content": path.read_text(encoding="utf-8")}

    if op == "write":
        content = args.get("content")
        if not isinstance(content, str):
            return {"error": "invalid_args", "detail": "content string required for write"}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": _rel(workspace, path), "bytes": len(content.encode("utf-8"))}

    if op == "str_replace":
        old = args.get("old_string")
        new = args.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return {"error": "invalid_args", "detail": "old_string and new_string required"}
        if not path.is_file():
            return {"error": "not_found", "path": _rel(workspace, path)}
        text = path.read_text(encoding="utf-8")
        if old not in text:
            return {"error": "old_string_not_found", "path": _rel(workspace, path)}
        replace_all = bool(args.get("replace_all", False))
        if replace_all:
            updated = text.replace(old, new)
            count = text.count(old)
        else:
            updated = text.replace(old, new, 1)
            count = 1
        path.write_text(updated, encoding="utf-8")
        return {"ok": True, "path": _rel(workspace, path), "replacements": count}

    return {"error": "invalid_op", "op": op, "allowed": ["read", "write", "str_replace"]}


def _resolve_protocol_file(workspace: Path, raw: str) -> Path | None:
    """Resolve a protocol path, coercing mistaken ``../`` prefixes into the workspace."""
    coerced = coerce_path_into_workspace(raw, workspace)
    for candidate in (Path(coerced), workspace / coerced, Path(raw), workspace / raw):
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.is_file():
            try:
                resolved.relative_to(workspace.resolve())
            except ValueError:
                # Absolute path outside workspace is still usable for MCP upload.
                pass
            return resolved
    return None


def _resolve_under(workspace: Path, rel: str) -> Path:
    workspace = workspace.resolve()
    # Disallow absolute escapes via .. after resolve
    candidate = (workspace / rel).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {rel}") from exc
    return candidate


def _rel(workspace: Path, path: Path) -> str:
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


# --- robot -----------------------------------------------------------------


def _fetch_run_status(host: str, run_id: Any) -> str | None:
    history = call_tool(
        "run_history",
        {"robot_ip": host, "run_id": run_id},
        timeout_sec=30,
    )
    data = history.get("data") if isinstance(history.get("data"), dict) else history
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    return str(status).strip().lower() if status else None


def _attach_active_run_status(
    out: dict[str, Any],
    host: str,
    run_id: Any,
    *,
    status: str | None = None,
) -> None:
    if status:
        out["active_run_status"] = status
        return
    if not run_id:
        return
    fetched = _fetch_run_status(host, run_id)
    if fetched:
        out["active_run_status"] = fetched


def _status_from_watch_payload(watched: dict[str, Any]) -> str | None:
    data = watched.get("data") if isinstance(watched.get("data"), dict) else watched
    if not isinstance(data, dict):
        return None
    for key in ("status", "final_status", "run_status"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()
    return None


def _resume_play_blocked(
    *,
    host: str,
    run_id: Any,
    action_key: str,
    call_payload: dict[str, Any],
) -> dict[str, Any] | None:
    play = action_key in {"resume_run", "play_run"} or (
        action_key == "control_run" and str(call_payload.get("action") or "").lower() == "play"
    )
    if not play or not run_id:
        return None
    status = _fetch_run_status(host, run_id)
    if status not in RESUME_BLOCKED_RUN_STATUSES:
        return None
    return {
        "op": "act",
        "error": "resume_blocked",
        "run_id": run_id,
        "run_status": status,
        "detail": (
            f"resume_run/play blocked while run status is {status}. "
            "Do not replay the failed run. Call recover_liquid_source_substitution "
            "(one-step L0, like recover_tip_pickup)."
        ),
        "recommended_next_tools": [
            "recover_liquid_source_substitution",
            "execute_protocol_recovery",
        ],
    }


_LOCAL_ROBOT_ACTS = frozenset(
    {
        "simulate_protocol",
        "run_pressure_trace",
        "analyze_pressure_trace",
        "fetch_pressure_trace",
    }
)


def _truthy_execute_on_robot(args: dict) -> bool:
    extra = args.get("args") if isinstance(args.get("args"), dict) else {}
    value = extra.get("execute_on_robot", args.get("execute_on_robot"))
    if value is True:
        return True
    if isinstance(value, str) and value.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return False


def _is_local_robot_act(args: dict) -> bool:
    """Simulate-only pressure / local analyze / simulate_protocol need no robot_ip."""
    if str(args.get("op") or "") != "act":
        return False
    action = resolve_robot_act_label(args)
    if action not in _LOCAL_ROBOT_ACTS:
        return False
    if action in {"analyze_pressure_trace", "simulate_protocol"}:
        return True
    return not _truthy_execute_on_robot(args)


def _robot(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    op = str(args.get("op") or "")
    host = robot_ip or session.get("robot_ip") or args.get("robot_ip")
    local_act = _is_local_robot_act(args)
    if not host:
        if not local_act:
            return {
                "error": "robot_ip_missing",
                "op": op,
                "detail": "No robot_ip provided; set robot_ip or session['robot_ip'].",
            }
        base = "local"
        host_str: str | None = None
    else:
        try:
            base = normalize_robot_base(str(host))
        except ValueError as exc:
            return {"error": "invalid_robot_ip", "detail": str(exc)}
        host_str = str(host)

    run_id = args.get("run_id") or session.get("run_id") or session.get("active_run_id")
    session_id = args.get("session_id") or session.get("session_id")
    extra = args.get("args") if isinstance(args.get("args"), dict) else {}

    if op == "status":
        if not host_str:
            return {
                "error": "robot_ip_missing",
                "op": op,
                "detail": "No robot_ip provided; set robot_ip or session['robot_ip'].",
            }
        return _robot_status(
            host=host_str,
            base=base,
            run_id=run_id,
            session_id=session_id,
            include_modules=bool(args.get("include_modules", True)),
            workspace=workspace,
        )
    if op == "watch":
        if not host_str:
            return {
                "error": "robot_ip_missing",
                "op": op,
                "detail": "No robot_ip provided; set robot_ip or session['robot_ip'].",
            }
        return _robot_watch(
            host=host_str,
            base=base,
            run_id=run_id,
            session_id=session_id,
            prefer_outbox=bool(args.get("prefer_outbox", False)),
            extra=extra,
            workspace=workspace,
        )
    if op == "act":
        if _truthy_execute_on_robot(args) and not host_str:
            return {
                "error": "robot_ip_missing",
                "op": op,
                "detail": "execute_on_robot requires robot_ip.",
            }
        return _robot_act(
            host=host_str,
            base=base,
            run_id=run_id,
            session_id=session_id,
            recovery_branch=args.get("recovery_branch"),
            action=args.get("action") or args.get("action_type"),
            extra=extra,
            raw_args=args,
            workspace=workspace,
        )
    return {"error": "invalid_op", "op": op, "allowed": ["status", "watch", "act"]}


def _robot_status(
    *,
    host: str,
    base: str,
    run_id: Any,
    session_id: Any,
    include_modules: bool,
    workspace: Path | None = None,
) -> dict:
    mcp_args: dict[str, Any] = {"robot_ip": host}
    if run_id:
        mcp_args["run_id"] = run_id
    if session_id:
        mcp_args["session_id"] = session_id
    # Symmetry with _robot_watch: time_window enrichment needs protocol source.
    if workspace is not None:
        _maybe_attach_protocol_path(mcp_args, workspace)

    robot_status = call_tool("robot_status", mcp_args)
    out: dict[str, Any] = {
        "op": "status",
        "robot_base": base,
        "robot_status": robot_status,
    }
    if include_modules:
        out["module_status"] = call_tool("module_status", mcp_args)
    if run_id:
        recovery_args = dict(mcp_args)
        if workspace is not None:
            _maybe_attach_protocol_path(recovery_args, workspace)
        out["parse_error"] = call_tool("parse_error", recovery_args)
        suggest = call_tool("suggest_recovery_action", recovery_args)
        out["suggest_recovery"] = suggest
        recovery = ((suggest.get("data") or {}).get("recovery") or {})
        tip_budget = recovery.get("tip_budget")
        if tip_budget:
            out["tip_budget"] = tip_budget
        if recovery.get("action") == "manual_only" and recovery.get("recommended_manual_action") == "escalate_tip_search_exhausted":
            out["tip_budget_blocked"] = True
            out["tip_budget_message"] = (
                (tip_budget or {}).get("message")
                or "Tip budget insufficient; do not retry pickup or resume."
            )
        if recovery.get("action") in {
            "substitute_liquid_source_with_attached_tip",
        }:
            out["liquid_substitution_recovery"] = {
                "failed_source_key": recovery.get("failed_source_key") or recovery.get("source_map_key"),
                "preferred_source_key": recovery.get("preferred_source_key"),
                "candidates": recovery.get("same_liquid_source_candidates") or [],
                "next_tools": recovery.get("recommended_next_tools") or [],
            }
        volume_check = recovery.get("volume_check")
        if isinstance(volume_check, dict):
            out["volume_check"] = volume_check
        blocked_reason = recovery.get("blocked_reason")
        if isinstance(blocked_reason, str) and blocked_reason.strip():
            out["blocked_reason"] = blocked_reason.strip()
    if _is_error_payload(robot_status) and not run_id:
        out["error"] = robot_status.get("error") or "robot_status_failed"
    _attach_active_run_status(out, host, run_id)
    return out


def _robot_watch(
    *,
    host: str,
    base: str,
    run_id: Any,
    session_id: Any,
    prefer_outbox: bool,
    extra: dict,
    workspace: Path | None = None,
) -> dict:
    if prefer_outbox or (not run_id and session_id):
        outbox_args: dict[str, Any] = {"limit": int(extra.get("limit", 20))}
        if session_id:
            outbox_args["session_id"] = session_id
        if run_id:
            outbox_args["run_id"] = run_id
        outbox = call_tool("runtime_get_outbox", outbox_args)
        if not _is_error_payload(outbox):
            return {"op": "watch", "robot_base": base, "source": "outbox", "outbox": outbox}

    if run_id:
        watch_args: dict[str, Any] = {
            "robot_ip": host,
            "run_id": run_id,
            "max_block_ms": int(extra.get("max_block_ms", 5000)),
            "poll_interval_ms": int(extra.get("poll_interval_ms", 1000)),
        }
        if session_id:
            watch_args["session_id"] = session_id
        for key in ("tiprack_slots",):
            if key in extra:
                watch_args[key] = extra[key]
        if workspace is not None:
            _maybe_attach_protocol_path(watch_args, workspace)
        watched = call_tool("runtime_watch_poll", watch_args, timeout_sec=WATCH_TIMEOUT_SEC)
        # Fall back to status only when the MCP tool itself is missing/unloadable.
        stderr = str(watched.get("stderr", ""))
        tool_missing = watched.get("error") in {
            "mcp_index_missing",
            "mcp_tool_spawn_failed",
        } or (
            watched.get("error") == "mcp_tool_failed" and "Unknown MCP tool" in stderr
        )
        if not tool_missing:
            out = {
                "op": "watch",
                "robot_base": base,
                "source": "runtime_watch_poll",
                "watch": watched,
            }
            _attach_active_run_status(
                out,
                host,
                run_id,
                status=_status_from_watch_payload(watched),
            )
            return out

    # Degrade to status
    degraded = _robot_status(
        host=host,
        base=base,
        run_id=run_id,
        session_id=session_id,
        include_modules=True,
        workspace=workspace,
    )
    degraded["op"] = "watch"
    degraded["source"] = "status_fallback"
    _attach_active_run_status(degraded, host, run_id)
    return degraded


_ACT_ALIASES: dict[str, tuple[str, dict[str, Any]]] = {
    "execute_recovery_branch": ("execute_protocol_recovery", {}),
    "execute_protocol_recovery": ("execute_protocol_recovery", {}),
    "pause_run": ("control_run", {"action": "pause"}),
    "resume_run": ("control_run", {"action": "play"}),
    "play_run": ("control_run", {"action": "play"}),
    "abort_run": ("control_run", {"action": "stop"}),
    "stop_run": ("control_run", {"action": "stop"}),
    "stop": ("control_run", {"action": "stop"}),
    "inspect_robot_state": ("robot_status", {}),
    "simulate_protocol": ("simulate_protocol", {}),
    "capture_deck_image": ("capture_preview_image", {}),
    "record_liquid_source_map": ("record_liquid_source_map", {}),
    "recover_liquid_source_substitution": ("recover_liquid_source_substitution", {}),
    "run_protocol": ("run_protocol", {}),
}


def _mcp_plugin_data_dir() -> Path:
    return plugins_mcp_index().parent / ".plugin-data"


def _protocol_path_from_mcp_artifacts(run_id: Any) -> str | None:
    if not run_id:
        return None
    rid = str(run_id)
    session_file = _mcp_plugin_data_dir() / "session-state" / f"{rid}.json"
    if session_file.is_file():
        try:
            payload = json.loads(session_file.read_text(encoding="utf-8"))
            candidate = payload.get("protocol_path")
            if candidate:
                path = Path(str(candidate)).expanduser()
                if path.is_file():
                    return str(path.resolve())
        except (OSError, json.JSONDecodeError):
            pass
    log_file = _mcp_plugin_data_dir() / "result-logs" / f"{rid}.jsonl"
    if log_file.is_file():
        try:
            for line in reversed(log_file.read_text(encoding="utf-8").splitlines()):
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                for key in ("protocol_path",):
                    candidate = entry.get(key) or (entry.get("data") or {}).get(key)
                    if not candidate and (entry.get("data") or {}).get("file_path"):
                        candidate = (entry.get("data") or {}).get("file_path")
                    if candidate:
                        path = Path(str(candidate)).expanduser()
                        if path.is_file():
                            return str(path.resolve())
        except (OSError, json.JSONDecodeError):
            pass
    return None


def _protocol_path_from_local_workspace(workspace: Path, protocol_name: str | None = None) -> str | None:
    local_dir = workspace / "local"
    if not local_dir.is_dir():
        return None
    py_files = sorted(p for p in local_dir.glob("*.py") if p.is_file())
    if len(py_files) == 1:
        return str(py_files[0].resolve())
    if protocol_name:
        needle = str(protocol_name).strip()
        for candidate in py_files:
            try:
                source = candidate.read_text(encoding="utf-8")
            except OSError:
                continue
            if (
                f'"protocolName": "{needle}"' in source
                or f'"protocolName":"{needle}"' in source
                or f"'protocolName': '{needle}'" in source
            ):
                return str(candidate.resolve())
    return None


def _maybe_attach_protocol_path(payload: dict[str, Any], workspace: Path) -> None:
    """Help recovery classify tip binding by attaching a local protocol path when omitted."""
    if payload.get("file_path") or payload.get("protocol_path") or payload.get("protocol_source"):
        return
    env_path = os.environ.get("LABSCRIPTAI_PROTOCOL_PATH")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_file():
            payload["file_path"] = str(candidate.resolve())
            return
    artifact_path = _protocol_path_from_mcp_artifacts(payload.get("run_id"))
    if artifact_path:
        payload["file_path"] = artifact_path
        return
    local_match = _protocol_path_from_local_workspace(
        workspace,
        protocol_name=payload.get("protocol_name"),
    )
    if local_match:
        payload["file_path"] = local_match


def _robot_act(
    *,
    host: str | None,
    base: str,
    run_id: Any,
    session_id: Any,
    recovery_branch: Any,
    action: Any,
    extra: dict,
    raw_args: dict,
    workspace: Path,
) -> dict:
    skip = {
        "op",
        "args",
        "action",
        "action_type",
        "type",
        "recovery_branch",
        "include_modules",
        "prefer_outbox",
        "robot_ip",
    }
    passthrough = {k: v for k, v in raw_args.items() if k not in skip}
    payload: dict[str, Any] = {**passthrough, **extra}
    if host:
        payload["robot_ip"] = host
    if run_id and "run_id" not in payload:
        payload["run_id"] = run_id
    if session_id and "session_id" not in payload:
        payload["session_id"] = session_id

    branch = recovery_branch or payload.get("recovery_branch") or payload.get("branch")
    action_key = str(action).strip() if isinstance(action, str) else ""

    # Prefer recovery when branch is set or action aliases to recovery.
    if branch or action_key in {"execute_recovery_branch", "execute_protocol_recovery"}:
        if branch:
            payload["recovery_branch"] = branch
        _maybe_attach_protocol_path(payload, workspace)
        if not payload.get("run_id"):
            return {
                "error": "run_id_required",
                "op": "act",
                "detail": "execute_protocol_recovery requires run_id",
            }
        if not payload.get("recovery_branch"):
            return {
                "error": "recovery_branch_required",
                "op": "act",
                "detail": "execute_protocol_recovery requires recovery_branch",
            }
        payload.setdefault("timeout_ms", 1_800_000)
        payload.setdefault("poll_interval_ms", 1000)
        result = call_tool(
            "execute_protocol_recovery",
            payload,
            timeout_sec=RUN_PROTOCOL_TIMEOUT_SEC,
        )
        return {
            "op": "act",
            "robot_base": base,
            "tool": "execute_protocol_recovery",
            "result": result,
        }

    if action_key:
        tool_name, injected = _ACT_ALIASES.get(action_key, (action_key, {}))
        call_payload = {**payload, **injected}
        # create_run needs protocol_id. Agents often pass protocol_path alone, which
        # creates an empty run that plays to succeeded with 0 commands (no motion).
        # Rewrite to run_protocol (upload + create + play) when a local file is given.
        if tool_name == "create_run" and not call_payload.get("protocol_id"):
            proto = call_payload.get("file_path") or call_payload.get("protocol_path")
            if isinstance(proto, str) and proto.strip():
                resolved = _resolve_protocol_file(workspace, proto)
                if resolved is not None:
                    call_payload["file_path"] = str(resolved)
                    call_payload.pop("protocol_path", None)
                    tool_name = "run_protocol"
                else:
                    return {
                        "error": "protocol_file_not_found",
                        "op": "act",
                        "detail": (
                            "create_run with protocol_path requires an existing .py file, "
                            "or pass protocol_id from upload_protocol first."
                        ),
                        "protocol_path": proto,
                    }
            else:
                return {
                    "error": "protocol_id_required",
                    "op": "act",
                    "detail": (
                        "create_run requires protocol_id (after upload_protocol), "
                        "or protocol_path/file_path to run via run_protocol."
                    ),
                }
        if host:
            blocked = _resume_play_blocked(
                host=host,
                run_id=call_payload.get("run_id") or run_id,
                action_key=action_key,
                call_payload=call_payload,
            )
            if blocked is not None:
                return blocked
        if tool_name in {
            "execute_protocol_recovery",
            "recover_tip_pickup",
            "recover_liquid_source_substitution",
        }:
            _maybe_attach_protocol_path(call_payload, workspace)
        if tool_name in {
            "run_protocol",
            "simulate_protocol",
            "doctor_local_runtime",
            "health_check",
            "recover_liquid_source_substitution",
            "execute_protocol_recovery",
            "recover_tip_pickup",
        }:
            call_payload.setdefault("operator_opt_in", True)
            call_payload.setdefault("timeout_ms", 1_800_000)
            call_payload.setdefault("poll_interval_ms", 1000)
            _ensure_python_executable(call_payload)
        if tool_name == "run_protocol":
            if not call_payload.get("file_path"):
                bundle_path = call_payload.get("recovery_bundle_path") or call_payload.get("bundle_path")
                if isinstance(bundle_path, str) and bundle_path.strip():
                    try:
                        bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
                        generated = bundle.get("generated_protocol_path")
                        if generated:
                            call_payload["file_path"] = generated
                    except (OSError, json.JSONDecodeError):
                        pass
                if not call_payload.get("file_path") and call_payload.get("protocol_path"):
                    call_payload["file_path"] = str(call_payload["protocol_path"])
            if isinstance(call_payload.get("file_path"), str):
                resolved = _resolve_protocol_file(workspace, call_payload["file_path"])
                if resolved is not None:
                    call_payload["file_path"] = str(resolved)
            _ensure_python_executable(call_payload)
            call_payload.setdefault("operator_opt_in", True)
            call_payload.setdefault("timeout_ms", 1_800_000)
            call_payload.setdefault("poll_interval_ms", 1000)
            result = call_tool(
                tool_name,
                call_payload,
                timeout_sec=RUN_PROTOCOL_TIMEOUT_SEC,
            )
            return {"op": "act", "robot_base": base, "tool": tool_name, "result": result}
        if tool_name in {
            "recover_liquid_source_substitution",
            "execute_protocol_recovery",
            "recover_tip_pickup",
        }:
            result = call_tool(
                tool_name,
                call_payload,
                timeout_sec=RUN_PROTOCOL_TIMEOUT_SEC,
            )
            return {"op": "act", "robot_base": base, "tool": tool_name, "result": result}
        if tool_name == "upload_protocol" and isinstance(call_payload.get("file_path"), str):
            resolved = _resolve_protocol_file(workspace, call_payload["file_path"])
            if resolved is not None:
                call_payload["file_path"] = str(resolved)
        # control_run uses action=pause|play|stop — don't leave action_type clutter
        result = call_tool(tool_name, call_payload)
        return {"op": "act", "robot_base": base, "tool": tool_name, "result": result}

    return {
        "error": "invalid_act",
        "op": "act",
        "detail": "Provide recovery_branch (→ execute_protocol_recovery) or action / action_type.",
        "robot_base": base,
    }


def _is_error_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and bool(payload.get("error"))


# --- memory ----------------------------------------------------------------


def _memory(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    del robot_ip, session
    op = str(args.get("op") or "")
    mem_root = (workspace / _MEMORY_DIRNAME).resolve()
    try:
        mem_root.relative_to(workspace)
    except ValueError:
        return {"error": "path_escape", "detail": "memory root escaped workspace"}

    if op == "list":
        if not mem_root.is_dir():
            return {"op": "list", "notes": []}
        notes = sorted(p.name for p in mem_root.glob("*.md") if p.is_file())
        return {"op": "list", "notes": notes, "dir": _MEMORY_DIRNAME}

    if op == "search":
        query = str(args.get("query") or "").strip().lower()
        if not query:
            return {"error": "invalid_args", "detail": "query required for search"}
        limit = max(1, min(int(args.get("limit") or 10), 50))
        if not mem_root.is_dir():
            return {"op": "search", "hits": []}
        hits: list[dict[str, Any]] = []
        for path in sorted(mem_root.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            if query in text.lower() or query in path.name.lower():
                hits.append(
                    {
                        "name": path.name,
                        "snippet": _snippet(text, query),
                    }
                )
            if len(hits) >= limit:
                break
        return {"op": "search", "query": query, "hits": hits}

    name = args.get("name")
    if not isinstance(name, str) or not name.strip():
        return {"error": "invalid_args", "detail": "name required for read/write"}
    fname = name.strip()
    if not fname.endswith(".md"):
        fname = f"{fname}.md"
    if "/" in fname or "\\" in fname or ".." in fname:
        return {"error": "invalid_args", "detail": "name must be a bare filename"}
    path = (mem_root / fname).resolve()
    try:
        path.relative_to(mem_root)
    except ValueError:
        return {"error": "path_escape", "detail": "note path escapes memory dir"}

    if op == "read":
        if not path.is_file():
            return {"error": "not_found", "name": fname}
        return {"op": "read", "name": fname, "content": path.read_text(encoding="utf-8")}

    if op == "write":
        content = args.get("content")
        if not isinstance(content, str):
            return {"error": "invalid_args", "detail": "content string required for write"}
        mem_root.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "op": "write", "name": fname}

    return {"error": "invalid_op", "op": op, "allowed": ["read", "write", "list", "search"]}


def _snippet(text: str, query: str, radius: int = 80) -> str:
    lower = text.lower()
    idx = lower.find(query.lower())
    if idx < 0:
        return text[:160]
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    piece = text[start:end]
    if start > 0:
        piece = "…" + piece
    if end < len(text):
        piece = piece + "…"
    return piece


# --- skill -----------------------------------------------------------------


def _skill(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    del workspace, robot_ip, session
    root = _skills_dir()
    name = args.get("name")
    if name is None or (isinstance(name, str) and not name.strip()):
        skills = sorted(p.stem for p in root.glob("*.md") if p.is_file())
        return {"op": "list", "skills": skills, "dir": str(root)}
    stem = str(name).strip()
    if stem.endswith(".md"):
        stem = stem[:-3]
    if "/" in stem or "\\" in stem or ".." in stem:
        return {"error": "invalid_args", "detail": "name must be a bare skill stem"}
    path = (root / f"{stem}.md").resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return {"error": "path_escape", "detail": "skill path escaped skills dir"}
    if not path.is_file():
        available = sorted(p.stem for p in root.glob("*.md") if p.is_file())
        return {"error": "not_found", "name": stem, "available": available}
    return {"name": stem, "content": path.read_text(encoding="utf-8")}
