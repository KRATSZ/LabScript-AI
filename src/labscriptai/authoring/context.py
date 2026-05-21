"""Small context manager for authoring tool loops."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TOOL_RESULT_MAX_CHARS = 8000
TEXT_MAX_CHARS = 6000
CHARS_PER_TOKEN = 1.5


class ContextManager:
    def __init__(self, transcript_dir: Path | str | None = None) -> None:
        self.transcript_dir = Path(transcript_dir) if transcript_dir else None
        if self.transcript_dir:
            self.transcript_dir.mkdir(parents=True, exist_ok=True)

    def micro_compact(self, messages: list[dict[str, Any]]) -> None:
        for message in messages[-20:]:
            content = message.get("content")
            if isinstance(content, str) and len(content) > TEXT_MAX_CHARS:
                message["content"] = content[:TEXT_MAX_CHARS] + "\n\n...(truncated)"

    def estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        total = 0
        for message in messages:
            total += len(json.dumps(message, ensure_ascii=False))
        return int(total / CHARS_PER_TOKEN)
