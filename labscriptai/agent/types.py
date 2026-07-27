"""Minimal shared dataclasses for the lean agent (W1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """Normalized model tool call (matches llm.complete tool_calls entries)."""

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
