"""Lean agent tools: bash, edit, robot, memory, skill.

``execute`` runs tools already allowed by the outer gate — no gating here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .mcp_adapter import (
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
_MAX_BASH_OUTPUT = 50_000


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
                "op=status|watch|act. parse_error/suggest_recovery embed under status when run_id is set."
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


def _clip(text: str, limit: int = _MAX_BASH_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…[truncated {len(text) - limit} chars]"


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


def _robot(
    args: dict,
    *,
    workspace: Path,
    robot_ip: str | None,
    session: dict,
) -> dict:
    del workspace
    op = str(args.get("op") or "")
    host = robot_ip or session.get("robot_ip") or args.get("robot_ip")
    if not host:
        return {
            "error": "robot_ip_missing",
            "op": op,
            "detail": "No robot_ip provided; set robot_ip or session['robot_ip'].",
        }
    try:
        base = normalize_robot_base(str(host))
    except ValueError as exc:
        return {"error": "invalid_robot_ip", "detail": str(exc)}

    run_id = args.get("run_id") or session.get("run_id") or session.get("active_run_id")
    session_id = args.get("session_id") or session.get("session_id")
    extra = args.get("args") if isinstance(args.get("args"), dict) else {}

    if op == "status":
        return _robot_status(
            host=str(host),
            base=base,
            run_id=run_id,
            session_id=session_id,
            include_modules=bool(args.get("include_modules", True)),
        )
    if op == "watch":
        return _robot_watch(
            host=str(host),
            base=base,
            run_id=run_id,
            session_id=session_id,
            prefer_outbox=bool(args.get("prefer_outbox", False)),
            extra=extra,
        )
    if op == "act":
        return _robot_act(
            host=str(host),
            base=base,
            run_id=run_id,
            session_id=session_id,
            recovery_branch=args.get("recovery_branch"),
            action=args.get("action") or args.get("action_type"),
            extra=extra,
            raw_args=args,
        )
    return {"error": "invalid_op", "op": op, "allowed": ["status", "watch", "act"]}


def _robot_status(
    *,
    host: str,
    base: str,
    run_id: Any,
    session_id: Any,
    include_modules: bool,
) -> dict:
    mcp_args: dict[str, Any] = {"robot_ip": host}
    if run_id:
        mcp_args["run_id"] = run_id
    if session_id:
        mcp_args["session_id"] = session_id

    robot_status = call_tool("robot_status", mcp_args)
    out: dict[str, Any] = {
        "op": "status",
        "robot_base": base,
        "robot_status": robot_status,
    }
    if include_modules:
        out["module_status"] = call_tool("module_status", mcp_args)
    if run_id:
        out["parse_error"] = call_tool("parse_error", mcp_args)
        out["suggest_recovery"] = call_tool("suggest_recovery_action", mcp_args)
    if _is_error_payload(robot_status) and not run_id:
        out["error"] = robot_status.get("error") or "robot_status_failed"
    return out


def _robot_watch(
    *,
    host: str,
    base: str,
    run_id: Any,
    session_id: Any,
    prefer_outbox: bool,
    extra: dict,
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
            return {"op": "watch", "robot_base": base, "source": "runtime_watch_poll", "watch": watched}

    # Degrade to status
    degraded = _robot_status(
        host=host,
        base=base,
        run_id=run_id,
        session_id=session_id,
        include_modules=True,
    )
    degraded["op"] = "watch"
    degraded["source"] = "status_fallback"
    return degraded


_ACT_ALIASES: dict[str, tuple[str, dict[str, Any]]] = {
    "execute_recovery_branch": ("execute_protocol_recovery", {}),
    "execute_protocol_recovery": ("execute_protocol_recovery", {}),
    "pause_run": ("control_run", {"action": "pause"}),
    "resume_run": ("control_run", {"action": "play"}),
    "abort_run": ("control_run", {"action": "stop"}),
    "inspect_robot_state": ("robot_status", {}),
    "simulate_protocol": ("simulate_protocol", {}),
    "capture_deck_image": ("capture_preview_image", {}),
}


def _robot_act(
    *,
    host: str,
    base: str,
    run_id: Any,
    session_id: Any,
    recovery_branch: Any,
    action: Any,
    extra: dict,
    raw_args: dict,
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
    payload: dict[str, Any] = {"robot_ip": host, **passthrough, **extra}
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
        result = call_tool("execute_protocol_recovery", payload)
        return {
            "op": "act",
            "robot_base": base,
            "tool": "execute_protocol_recovery",
            "result": result,
        }

    if action_key:
        tool_name, injected = _ACT_ALIASES.get(action_key, (action_key, {}))
        call_payload = {**payload, **injected}
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
