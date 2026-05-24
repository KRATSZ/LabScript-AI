"""Minimal ReAct ReAct authoring loop."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from json import JSONDecodeError
from urllib import error, request

from labscriptai.benchmark.package_validator import REQUIRED_PACKAGE_FILES
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.runtime.model_adapter import OpenAICompatibleConfig, _strip_json_markdown
from labscriptai.runtime.trace import TraceEvent, TraceWriter

from .context import ContextManager
from .prompts import AUTHORING_AGENT_SYSTEM_PROMPT
from .skills import SkillLoader
from .task_state import AuthoringTaskState
from .tools import AuthoringToolRegistry


class AuthoringClient(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        ...


class OpenAICompatibleAuthoringClient:
    def __init__(self, config: OpenAICompatibleConfig, *, opener: Any | None = None) -> None:
        self.config = config
        self.opener = opener or request.urlopen
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.config.max_tokens,
            "thinking": {"type": "disabled"},
            "tools": _native_tool_specs(tools),
            "tool_choice": "auto",
        }
        req = request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with self.opener(req, timeout=self.config.timeout_sec) as response:
                raw_response = response.read()
                _write_provider_debug(
                    provider="authoring",
                    stage="response",
                    status=getattr(response, "status", None),
                    headers=dict(response.headers.items()) if getattr(response, "headers", None) else {},
                    body=raw_response,
                    error_message=None,
                )
                response_payload = json.loads(raw_response.decode("utf-8"))
        except error.HTTPError as exc:
            raw_response = exc.read()
            _write_provider_debug(
                provider="authoring",
                stage="http_error",
                status=exc.code,
                headers=dict(exc.headers.items()) if exc.headers else {},
                body=raw_response,
                error_message=str(exc),
            )
            raise
        usage = response_payload.get("usage")
        if isinstance(usage, dict):
            input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
            total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.total_tokens += total_tokens
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("model response missing choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ValueError("model response missing message")
        tool_calls = message.get("tool_calls")
        if isinstance(tool_calls, list) and tool_calls:
            normalized = []
            for call in tool_calls:
                function = call.get("function", {}) if isinstance(call, dict) else {}
                args = function.get("arguments", "{}")
                normalized.append(
                    {
                        "id": call.get("id") if isinstance(call, dict) else None,
                        "name": function.get("name"),
                        "arguments": json.loads(args) if isinstance(args, str) else args,
                    }
                )
            return {
                "tool_calls": normalized,
                "_assistant_message": {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                },
            }
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            finish_reason = choices[0].get("finish_reason") if isinstance(choices[0], dict) else None
            raise ValueError(f"model response content is empty; finish_reason={finish_reason}")
        return _load_first_json_object(content)


def _write_provider_debug(
    *,
    provider: str,
    stage: str,
    status: int | None,
    headers: dict[str, Any],
    body: bytes,
    error_message: str | None,
) -> None:
    debug_dir = os.environ.get("LABSCRIPTAI_PROVIDER_DEBUG_DIR")
    if not debug_dir:
        return
    path = Path(debug_dir)
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    safe_headers = {
        str(key): str(value)
        for key, value in headers.items()
        if str(key).lower() not in {"authorization", "proxy-authorization", "set-cookie", "cookie"}
    }
    text = body.decode("utf-8", errors="replace")
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "stage": stage,
        "status": status,
        "headers": safe_headers,
        "body_length": len(body),
        "body_prefix": text[:4000],
        "body_suffix": text[-4000:] if len(text) > 4000 else text,
        "error": error_message,
    }
    (path / f"{timestamp}-{provider}-{stage}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _load_first_json_object(content: str) -> dict[str, Any]:
    stripped = _strip_json_markdown(content)
    decoder = json.JSONDecoder()
    try:
        parsed = json.loads(stripped)
    except JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise
        parsed, _ = decoder.raw_decode(stripped[start:])
    if not isinstance(parsed, dict):
        raise ValueError("model response JSON must be an object")
    return parsed


def _native_tool_specs(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {
        "load_skill": {
            "description": "Load a concise authoring skill by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        "search_protocol_library": {
            "description": "Search reference Opentrons protocols by keyword.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        "read_file": {
            "description": "Read a file from the package directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
        "write_file": {
            "description": "Write a complete file inside the package directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        },
        "str_replace": {
            "description": "Replace exact text in a package file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "replace_all": {"type": "boolean"},
                },
                "required": ["path", "old", "new"],
            },
        },
        "json_set": {
            "description": "Set one value in a JSON package file using an RFC 6901 JSON pointer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pointer": {"type": "string"},
                    "value": {},
                    "create_missing": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["path", "pointer", "value"],
            },
        },
        "append_md": {
            "description": "Append Markdown text to a package Markdown file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["path", "text"],
            },
        },
        "run_simulate": {
            "description": "Run Opentrons simulation for package protocol.py.",
            "parameters": {"type": "object", "properties": {}},
        },
        "validate_package": {
            "description": "Run deterministic package validation.",
            "parameters": {
                "type": "object",
                "properties": {"simulation_pass": {"type": "boolean"}},
            },
        },
        "robot.inspect": {
            "description": "Read robot or run status without moving hardware.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "enum": ["http", "mcp"]},
                    "host": {"type": "string"},
                    "robot_ip": {"type": "string"},
                    "port": {"type": "integer"},
                    "run_id": {"type": "string"},
                },
            },
        },
        "error.parse": {
            "description": "Parse a runtime, simulation, or robot error into a useful category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_error": {"type": "string"},
                    "run_id": {"type": "string"},
                },
            },
        },
        "recovery.suggest": {
            "description": "Ask the recovery backend for a safe recovery suggestion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "robot_ip": {"type": "string"},
                    "run_id": {"type": "string"},
                    "error": {},
                },
            },
        },
        "run.control": {
            "description": "Propose a gated runtime control action. Hardware-affecting actions require approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "reason": {"type": "string"},
                    "human_confirmed": {"type": "boolean"},
                    "branch": {"type": "string"},
                    "patch": {"type": "object"},
                    "dry_run": {"type": "boolean"},
                },
                "required": ["action_type"],
            },
        },
        "package.read_write": {
            "description": "Read or edit files inside the current protocol package directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["read", "write", "str_replace", "json_set", "append_md"]},
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                    "pointer": {"type": "string"},
                    "value": {},
                    "text": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["op", "path"],
            },
        },
        "package.validate": {
            "description": "Validate the current protocol package.",
            "parameters": {
                "type": "object",
                "properties": {"simulation_pass": {"type": "boolean"}},
            },
        },
        "package.simulate": {
            "description": "Simulate the current protocol package.",
            "parameters": {"type": "object", "properties": {}},
        },
        "skill.search_load": {
            "description": "List or load concise LabscriptAI skills.",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["list", "load"]},
                    "name": {"type": "string"},
                },
                "required": ["op"],
            },
        },
        "memory.read_write": {
            "description": "Search or append runtime memory notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["search", "append"]},
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["op"],
            },
        },
        "protocol.search": {
            "description": "Search reference Opentrons protocols by keyword.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }
    native_tools = []
    for tool in tools:
        name = tool["name"]
        model_name = name.replace(".", "_")
        schema = schemas.get(name, {"description": f"LabscriptAI authoring tool {name}", "parameters": {}})
        native_tools.append(
            {
                "type": "function",
                "function": {
                    "name": model_name,
                    "description": schema["description"],
                    "parameters": schema["parameters"],
                },
            }
        )
    return native_tools


@dataclass(frozen=True)
class AuthoringAgentResult:
    package_dir: Path
    trace_path: Path
    tool_calls: int
    skill_loads: int
    simulator_calls: int
    completed: bool
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": str(self.package_dir),
            "trace_path": str(self.trace_path),
            "tool_calls": self.tool_calls,
            "skill_loads": self.skill_loads,
            "simulator_calls": self.simulator_calls,
            "completed": self.completed,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


class AuthoringAgent:
    def __init__(
        self,
        *,
        client: AuthoringClient,
        skill_loader: SkillLoader | None = None,
        max_steps: int = 12,
        skill_mode: str = "light",
        tool_profile: str = "kb",
    ) -> None:
        self.client = client
        self.skill_loader = skill_loader or SkillLoader()
        self.max_steps = max_steps
        if skill_mode not in {"full", "light", "off"}:
            raise ValueError("skill_mode must be one of: full, light, off")
        self.skill_mode = skill_mode
        if tool_profile not in {"edit", "simulate", "kb", "kb_strong"}:
            raise ValueError("tool_profile must be one of: edit, simulate, kb, kb_strong")
        self.tool_profile = tool_profile
        self.context = ContextManager()

    def run(
        self,
        *,
        task: AuthoringTask,
        package_dir: Path,
        trace_path: Path,
        opentrons_python: str | None = None,
        workspace_root: Path | None = None,
        simulation_timeout_sec: int = 180,
    ) -> AuthoringAgentResult:
        package_dir.mkdir(parents=True, exist_ok=True)
        run_id = f"authoring-{task.task_id}-{uuid.uuid4()}"
        state = AuthoringTaskState(run_id=run_id, task_id=task.task_id)
        writer = TraceWriter(trace_path)
        registry = AuthoringToolRegistry(
            package_dir=package_dir,
            trace_writer=writer,
            state=state,
            skill_loader=self.skill_loader,
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            simulation_timeout_sec=simulation_timeout_sec,
            skill_mode=self.skill_mode,
            tool_profile=self.tool_profile,
        )
        if self.tool_profile not in {"kb", "kb_strong"}:
            skill_catalog = "(KB disabled for this run)"
        elif self.skill_mode == "off":
            skill_catalog = "(skills disabled for this run)"
        elif self.tool_profile == "kb_strong":
            skill_catalog = "task templates: dilution, serial_dilution, plate_transfer, normalization, pcr_setup"
        elif self.skill_mode == "light":
            skill_catalog = "common_errors, deck_layout"
        else:
            skill_catalog = self.skill_loader.get_catalog() or "(none)"
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": AUTHORING_AGENT_SYSTEM_PROMPT.format(
                    skill_catalog=skill_catalog
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task_id": task.task_id,
                        "difficulty": task.difficulty,
                        "prompt": task.prompt,
                        "required_package_files": list(REQUIRED_PACKAGE_FILES),
                        "package_format_instruction": (
                            "Use the current three-piece v0.4 package even if the task text "
                            "mentions any older package format."
                        ),
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        completed = False
        writer.append(
            TraceEvent(run_id=run_id, event_type="state_update", actor="system", payload=state.to_dict())
        )
        for _ in range(self.max_steps):
            self.context.micro_compact(messages)
            response = self.client.complete(messages, registry.list_tool_specs())
            assistant_message = response.get("_assistant_message")
            if isinstance(assistant_message, dict):
                messages.append(assistant_message)
            else:
                messages.append({"role": "assistant", "content": json.dumps(response, ensure_ascii=False)})
            if isinstance(response.get("final"), dict):
                missing = [name for name in REQUIRED_PACKAGE_FILES if not (package_dir / name).exists()]
                if missing:
                    messages.append(
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "package_incomplete": {
                                        "missing_required_files": missing,
                                        "instruction": "Write the missing files before returning final.",
                                    }
                                },
                                ensure_ascii=False,
                            ),
                        }
                    )
                    continue
                completed = bool(response["final"].get("package_ready"))
                break
            calls = response.get("tool_calls")
            if not isinstance(calls, list) or not calls:
                break
            for call in calls:
                if not isinstance(call, dict):
                    continue
                name = str(call.get("name", ""))
                args = call.get("arguments")
                result = registry.call(name, args if isinstance(args, dict) else {})
                tool_call_id = call.get("id")
                if isinstance(tool_call_id, str) and tool_call_id:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(result.to_dict(), ensure_ascii=False),
                        }
                    )
                    continue
                messages.append(
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"tool_result": {"name": name, "result": result.to_dict()}},
                            ensure_ascii=False,
                        ),
                    }
                )
        registry.write_stats_file()
        stats_path = package_dir / "authoring_stats.json"
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        stats.update(
            {
                "input_tokens": int(getattr(self.client, "input_tokens", 0)),
                "output_tokens": int(getattr(self.client, "output_tokens", 0)),
                "total_tokens": int(getattr(self.client, "total_tokens", 0)),
            }
        )
        stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        writer.append(
            TraceEvent(
                run_id=run_id,
                event_type="summary",
                actor="system",
                payload={"completed": completed, **registry.state.to_dict()},
            )
        )
        return AuthoringAgentResult(
            package_dir=package_dir,
            trace_path=trace_path,
            tool_calls=registry.state.tool_calls,
            skill_loads=registry.state.skill_loads,
            simulator_calls=registry.state.simulator_calls,
            completed=completed,
            input_tokens=int(getattr(self.client, "input_tokens", 0)),
            output_tokens=int(getattr(self.client, "output_tokens", 0)),
            total_tokens=int(getattr(self.client, "total_tokens", 0)),
        )

    def run_to_files(self, *, task: AuthoringTask, work_dir: Path, **kwargs: Any) -> dict[str, str]:
        result = self.run(
            task=task,
            package_dir=work_dir / "package",
            trace_path=work_dir / "trace.jsonl",
            **kwargs,
        )
        _write_missing_metadata_files(result.package_dir, task)
        missing = [name for name in REQUIRED_PACKAGE_FILES if not (result.package_dir / name).exists()]
        if missing:
            raise ValueError(f"authoring agent did not produce required files: {missing}")
        files = {
            name: (result.package_dir / name).read_text(encoding="utf-8")
            for name in REQUIRED_PACKAGE_FILES
        }
        stats_path = result.package_dir / "authoring_stats.json"
        if stats_path.exists():
            files["authoring_stats.json"] = stats_path.read_text(encoding="utf-8")
        if result.trace_path.exists():
            files["trace.jsonl"] = result.trace_path.read_text(encoding="utf-8")
        return files


def _write_missing_metadata_files(package_dir: Path, task: AuthoringTask) -> None:
    defaults = {
        "setup_card.html": (
            f"<h1>Setup Card</h1>\n<p>Review generated protocol for task "
            f"{task.task_id} before execution.</p>\n"
        ),
        "manifest.json": {
            "schema_version": "0.4",
            "task_id": task.task_id,
            "system_id": "labscriptai",
            "model_id": "unknown",
            "scaffold_id": "labscriptai-authoring",
            "deck": {"slots": [], "modules": [], "instruments": []},
            "reagents": [],
            "tips": {"tips_required": 0, "tips_available": 0},
            "risk_flags": [],
            "critical_failures": [],
            "off_platform_handoff": {"declared": False},
            "tool_permissions": ["write_package_files", "validate_package", "simulate_protocol"],
            "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
        },
    }
    for name, content in defaults.items():
        path = package_dir / name
        if path.exists():
            continue
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")
