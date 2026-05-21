"""Registered tools for authoring ReAct loops."""

from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from labscriptai.benchmark.package_validator import validate_package
from labscriptai.runtime.trace import TraceEvent, TraceWriter, utc_now_iso

from ..skills import SkillLoader
from ..task_state import AuthoringTaskState


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    content: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, **self.content}


ToolFn = Callable[[dict[str, Any]], ToolResult]


class AuthoringToolRegistry:
    def __init__(
        self,
        *,
        package_dir: Path,
        trace_writer: TraceWriter | None = None,
        state: AuthoringTaskState,
        skill_loader: SkillLoader | None = None,
        opentrons_python: str | None = None,
        workspace_root: Path | None = None,
        simulation_timeout_sec: int = 180,
        skill_mode: str = "full",
    ) -> None:
        self.package_dir = package_dir
        self.trace_writer = trace_writer
        self.state = state
        self.skill_loader = skill_loader or SkillLoader()
        self.opentrons_python = opentrons_python
        self.workspace_root = workspace_root
        self.simulation_timeout_sec = simulation_timeout_sec
        if skill_mode not in {"full", "light", "off"}:
            raise ValueError("skill_mode must be one of: full, light, off")
        self.skill_mode = skill_mode
        self._tools: dict[str, ToolFn] = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "str_replace": self._str_replace,
            "json_set": self._json_set,
            "append_md": self._append_md,
            "run_simulate": self._run_simulate,
            "validate_package": self._validate_package,
            "search_protocol_library": self._search_protocol_library,
        }
        if skill_mode != "off":
            self._tools["load_skill"] = self._load_skill

    def list_tool_specs(self) -> list[dict[str, Any]]:
        return [{"name": name} for name in sorted(self._tools)]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        arguments = arguments or {}
        if name not in self._tools:
            return ToolResult(False, {"error": f"unknown tool: {name}"})
        self.state = self.state.with_counts(
            tool_calls=1,
            skill_loads=1 if name == "load_skill" else 0,
            simulator_calls=1 if name == "run_simulate" else 0,
        )
        if self.trace_writer:
            self.trace_writer.append(
                TraceEvent(
                    run_id=self.state.run_id,
                    event_type="tool_call",
                    actor="tool",
                    payload={"tool": name, "arguments": self._safe_args(arguments)},
                )
            )
        try:
            result = self._tools[name](arguments)
        except Exception as exc:  # pragma: no cover - defensive tool boundary.
            result = ToolResult(False, {"error": f"{type(exc).__name__}: {exc}"})
        if self.trace_writer:
            self.trace_writer.append(
                TraceEvent(
                    run_id=self.state.run_id,
                    event_type="tool_result",
                    actor="tool",
                    payload={"tool": name, "result": result.to_dict()},
                )
            )
        if name in {
            "write_file",
            "str_replace",
            "json_set",
            "append_md",
            "run_simulate",
            "validate_package",
        }:
            self._append_patch_log(name, arguments, result)
        return result

    def _safe_path(self, value: str) -> Path:
        rel = Path(value)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("path must be relative to package_dir")
        return self.package_dir / rel

    @staticmethod
    def _safe_args(arguments: dict[str, Any]) -> dict[str, Any]:
        safe = dict(arguments)
        if "content" in safe and isinstance(safe["content"], str):
            safe["content"] = f"<{len(safe['content'])} chars>"
        return safe

    def _read_file(self, arguments: dict[str, Any]) -> ToolResult:
        path = self._safe_path(str(arguments["path"]))
        if not path.exists():
            return ToolResult(False, {"error": "file not found", "path": str(path)})
        return ToolResult(True, {"path": str(path), "content": path.read_text(encoding="utf-8")})

    def _write_file(self, arguments: dict[str, Any]) -> ToolResult:
        path = self._safe_path(str(arguments["path"]))
        content = str(arguments.get("content", ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResult(True, {"path": str(path), "bytes": len(content.encode("utf-8"))})

    def _str_replace(self, arguments: dict[str, Any]) -> ToolResult:
        path = self._safe_path(str(arguments["path"]))
        old = str(arguments["old"])
        new = str(arguments["new"])
        content = path.read_text(encoding="utf-8")
        count = content.count(old)
        if count == 0:
            return ToolResult(False, {"error": "old string not found", "path": str(path)})
        if count > 1 and not arguments.get("replace_all", False):
            return ToolResult(False, {"error": "old string occurs multiple times", "count": count})
        path.write_text(content.replace(old, new if arguments.get("replace_all", False) else new, 1 if not arguments.get("replace_all", False) else -1), encoding="utf-8")
        return ToolResult(True, {"path": str(path), "replacements": count if arguments.get("replace_all", False) else 1})

    def _json_set(self, arguments: dict[str, Any]) -> ToolResult:
        path = self._safe_path(str(arguments["path"]))
        pointer = str(arguments["pointer"])
        if not pointer.startswith("/"):
            return ToolResult(False, {"error": "pointer must be an RFC 6901 JSON pointer", "pointer": pointer})
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = {}
        created = bool(arguments.get("create_missing", True))
        value = arguments.get("value")
        try:
            updated = _json_pointer_set(payload, pointer, value, create_missing=created)
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            return ToolResult(False, {"error": str(exc), "path": str(path), "pointer": pointer})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return ToolResult(True, {"path": str(path), "pointer": pointer})

    def _append_md(self, arguments: dict[str, Any]) -> ToolResult:
        path = self._safe_path(str(arguments["path"]))
        text = str(arguments.get("text", ""))
        if not path.suffix.lower() in {".md", ".markdown"}:
            return ToolResult(False, {"error": "append_md only writes Markdown files", "path": str(path)})
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = path.read_text(encoding="utf-8") if path.exists() else ""
        separator = ""
        if previous and not previous.endswith("\n"):
            separator = "\n"
        if previous and text and not text.startswith("\n"):
            separator += "\n"
        path.write_text(previous + separator + text.rstrip() + "\n", encoding="utf-8")
        return ToolResult(True, {"path": str(path), "bytes_appended": len(text.encode("utf-8"))})

    def _run_simulate(self, arguments: dict[str, Any]) -> ToolResult:
        del arguments
        protocol_path = self.package_dir / "protocol.py"
        repo_root = Path(__file__).resolve().parents[4]
        verify_script = repo_root / "skills" / "opentrons-protocol-verify" / "scripts" / "verify_protocol.py"
        cmd = ["uv", "run", "python", str(verify_script), "simulate"]
        if self.workspace_root is not None:
            cmd.extend(["--workspace-root", str(self.workspace_root)])
        if self.opentrons_python:
            cmd.extend(["--python", self.opentrons_python])
        cmd.append(str(protocol_path))
        started = time.monotonic()
        try:
            completed = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.simulation_timeout_sec,
            )
            return ToolResult(
                completed.returncode == 0,
                {
                    "returncode": completed.returncode,
                    "duration_sec": time.monotonic() - started,
                    "stdout": completed.stdout[-6000:],
                    "stderr": completed.stderr[-6000:],
                    "command": cmd,
                },
            )
        except subprocess.TimeoutExpired as exc:
            return ToolResult(
                False,
                {
                    "returncode": None,
                    "duration_sec": time.monotonic() - started,
                    "stdout": exc.stdout or "",
                    "stderr": exc.stderr or "",
                    "error": f"simulation timed out after {self.simulation_timeout_sec}s",
                    "command": cmd,
                },
            )

    def _validate_package(self, arguments: dict[str, Any]) -> ToolResult:
        simulation_pass = bool(arguments.get("simulation_pass", False))
        result = validate_package(self.package_dir, simulation_pass=simulation_pass).to_dict()
        return ToolResult(bool(result.get("ok")), {"validation": result})

    def _search_protocol_library(self, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(False, {"error": "query is required"})
        repo_root = Path(__file__).resolve().parents[4]
        script = repo_root / "skills" / "opentrons-protocol-library" / "scripts" / "search_protocols.py"
        completed = subprocess.run(
            ["uv", "run", "python", str(script), "search", query],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        return ToolResult(
            completed.returncode == 0,
            {
                "query": query,
                "returncode": completed.returncode,
                "stdout": completed.stdout[-6000:],
                "stderr": completed.stderr[-2000:],
            },
        )

    def _load_skill(self, arguments: dict[str, Any]) -> ToolResult:
        name = str(arguments.get("name", ""))
        if self.skill_mode == "light" and name not in {"common_errors", "deck_layout"}:
            return ToolResult(
                False,
                {
                    "error": "skill disabled in light mode",
                    "available": ["common_errors", "deck_layout"],
                },
            )
        content = self.skill_loader.get_content(name)
        if content is None:
            return ToolResult(False, {"error": "unknown skill", "available": self.skill_loader.list_skills()})
        return ToolResult(True, {"name": name, "content": content})

    def _append_patch_log(
        self,
        name: str,
        arguments: dict[str, Any],
        result: ToolResult,
    ) -> None:
        entry = {
            "schema_version": "0.1",
            "entry_id": str(uuid.uuid4()),
            "timestamp": utc_now_iso(),
            "run_id": self.state.run_id,
            "tool": name,
            "target_path": arguments.get("path"),
            "reason": arguments.get("reason") or arguments.get("why") or "",
            "arguments": self._safe_args(arguments),
            "result": result.to_dict(),
        }
        path = self.package_dir / "authoring_patch_log.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def write_stats_file(self) -> None:
        (self.package_dir / "authoring_stats.json").write_text(
            json.dumps(self.state.to_dict(), indent=2),
            encoding="utf-8",
        )


def _json_pointer_set(
    payload: Any,
    pointer: str,
    value: Any,
    *,
    create_missing: bool,
) -> Any:
    parts = [_decode_json_pointer_part(part) for part in pointer.split("/")[1:]]
    if not parts:
        return value
    current = payload
    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]
        if isinstance(current, dict):
            if part not in current:
                if not create_missing:
                    raise KeyError(f"missing object key: {part}")
                current[part] = [] if _looks_like_list_index(next_part) else {}
            current = current[part]
            continue
        if isinstance(current, list):
            list_index = _parse_list_index(part, allow_append=False)
            if list_index >= len(current):
                if not create_missing:
                    raise IndexError(f"list index out of range: {part}")
                while len(current) <= list_index:
                    current.append({} if not _looks_like_list_index(next_part) else [])
            current = current[list_index]
            continue
        raise TypeError(f"cannot descend into {type(current).__name__} at {part}")
    final = parts[-1]
    if isinstance(current, dict):
        current[final] = value
        return payload
    if isinstance(current, list):
        if final == "-":
            current.append(value)
            return payload
        list_index = _parse_list_index(final, allow_append=False)
        if list_index > len(current):
            raise IndexError(f"list index out of range: {final}")
        if list_index == len(current):
            if not create_missing:
                raise IndexError(f"list index out of range: {final}")
            current.append(value)
        else:
            current[list_index] = value
        return payload
    raise TypeError(f"cannot set value on {type(current).__name__}")


def _decode_json_pointer_part(part: str) -> str:
    return part.replace("~1", "/").replace("~0", "~")


def _looks_like_list_index(part: str) -> bool:
    return part == "-" or part.isdigit()


def _parse_list_index(part: str, *, allow_append: bool) -> int:
    if part == "-" and allow_append:
        return -1
    if not part.isdigit():
        raise ValueError(f"list index must be a non-negative integer: {part}")
    return int(part)
