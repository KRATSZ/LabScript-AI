"""Append-only recovery patch log."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .trace import utc_now_iso


@dataclass(frozen=True)
class PatchLogEntry:
    run_id: str
    old_state_hash: str
    patch: Mapping[str, Any]
    reason: str
    gatekeeper_decision: Mapping[str, Any]
    human_confirmed: bool = False
    result: Mapping[str, Any] = field(default_factory=dict)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "old_state_hash": self.old_state_hash,
            "patch": dict(self.patch),
            "reason": self.reason,
            "gatekeeper_decision": dict(self.gatekeeper_decision),
            "human_confirmed": self.human_confirmed,
            "result": dict(self.result),
        }


class PatchLogWriter:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, entry: PatchLogEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def read_entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
