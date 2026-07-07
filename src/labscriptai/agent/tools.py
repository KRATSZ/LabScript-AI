"""Unified tool call/result primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Mapping, TypeAlias, get_args

from labscriptai.runtime.gatekeeper import GatekeeperDecision

# P1 keeps the spec-mandated ``agent/tools.py`` file and ``agent/tools/``
# wrapper directory. Exposing ``__path__`` lets ``labscriptai.agent.tools`` also
# load submodules such as ``labscriptai.agent.tools._legacy_names``.
__path__ = [str(Path(__file__).with_suffix(""))]

ToolName: TypeAlias = Literal[
    "package.read_write",
    "package.patch",
    "package.validate",
    "package.simulate",
    "robot.inspect",
    "run.control",
    "error.parse",
    "recovery.suggest",
    "skill.search_load",
    "memory.read_write",
    "protocol.search",
    "shell.run",
]
TOOL_NAMES = frozenset(get_args(ToolName))


@dataclass(frozen=True)
class ToolCall:
    name: ToolName
    arguments: Mapping[str, Any] = field(default_factory=dict)
    reason: str = ""
    proposed_by: str = "model"
    call_id: str | None = None

    @classmethod
    def from_model(cls, raw: Mapping[str, Any]) -> "ToolCall":
        from .tools._legacy_names import normalize_tool_call

        return normalize_tool_call(raw)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": _safe_args(self.arguments),
            "reason": self.reason,
            "proposed_by": self.proposed_by,
            "call_id": self.call_id,
        }


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    name: ToolName
    content: Mapping[str, Any]
    decision: GatekeeperDecision | None = None
    state_patch: Mapping[str, Any] = field(default_factory=dict)
    duration_ms: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "name": self.name,
            "content": dict(self.content),
            "decision": self.decision.to_dict() if self.decision else None,
            "state_patch": _jsonable_patch(self.state_patch),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


def _safe_args(arguments: Mapping[str, Any]) -> dict[str, Any]:
    safe = dict(arguments)
    for key in ("content", "diff"):
        if key in safe and isinstance(safe[key], str):
            safe[key] = f"<{len(safe[key])} chars>"
    return safe


def _jsonable_patch(patch: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(patch), default=str))
