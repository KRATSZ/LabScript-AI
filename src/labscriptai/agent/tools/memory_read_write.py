"""memory.read_write wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolResult
from labscriptai.runtime.memory import append_memory_note, search_memory


class MemoryReadWriteTool:
    name = "memory.read_write"

    def __init__(self, *, memory_dir: Path | str | None = None) -> None:
        self.memory_dir = Path(memory_dir) if memory_dir is not None else Path("runs/runtime_memory")

    def spec(self) -> dict[str, Any]:
        return {"name": self.name}

    def __call__(self, args: Mapping[str, Any], state: AgentState) -> ToolResult:
        op = str(args.get("op", "search"))
        if op == "append":
            path = append_memory_note(
                self.memory_dir,
                title=str(args.get("title", "runtime note")),
                body=str(args.get("body", "")),
                tags=tuple(str(tag) for tag in args.get("tags", ())),
                metadata=args.get("metadata") if isinstance(args.get("metadata"), Mapping) else None,
            )
            return ToolResult(True, self.name, {"path": str(path)})
        hits = tuple(
            search_memory(
                self.memory_dir,
                str(args.get("query", "")),
                limit=int(args.get("limit", 5)),
            )
        )
        return ToolResult(
            True,
            self.name,
            {"hits": [hit.to_dict() for hit in hits]},
            state_patch={"memory_hits": hits},
        )
