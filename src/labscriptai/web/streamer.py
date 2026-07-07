"""Server-Sent Events helpers for streaming trace.jsonl to web clients."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from labscriptai.runtime.trace import TraceEvent, TraceWriter

SSE_CONTENT_TYPE = "text/event-stream"
SSE_STREAMABLE_EVENT_TYPES = frozenset({"state_update", "tool_result"})


def format_sse_event(*, event: str, data: Mapping[str, Any], event_id: str | None = None) -> str:
    """Format one SSE frame with optional id, event name, and JSON payload."""

    lines: list[str] = []
    if event_id:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    payload = json.dumps(dict(data), ensure_ascii=False, sort_keys=True, default=str)
    lines.append(f"data: {payload}")
    lines.append("")
    return "\n".join(lines) + "\n"


def trace_event_to_sse(event: TraceEvent | Mapping[str, Any]) -> str:
    """Convert a trace event into an SSE string for the frontend contract."""

    payload = event.to_dict() if isinstance(event, TraceEvent) else dict(event)
    event_type = str(payload.get("event_type", "message"))
    event_id = str(payload.get("event_id") or "")
    return format_sse_event(event=event_type, data=payload, event_id=event_id or None)


def stream_trace_events(events: Iterator[TraceEvent | Mapping[str, Any]]) -> Iterator[str]:
    """Yield SSE strings for each trace event in order."""

    for event in events:
        yield trace_event_to_sse(event)


def stream_trace_jsonl(
    path: Path | str,
    *,
    event_types: frozenset[str] | None = None,
    poll_interval_sec: float = 0.25,
    keepalive_sec: float = 15.0,
) -> Iterator[str]:
    """Tail a trace.jsonl file and yield SSE frames as new events appear."""

    trace_path = Path(path)
    allowed = event_types or SSE_STREAMABLE_EVENT_TYPES
    offset = 0
    last_keepalive = time.monotonic()
    while True:
        if trace_path.exists():
            with trace_path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                for line in handle:
                    offset = handle.tell()
                    stripped = line.strip()
                    if not stripped:
                        continue
                    event = json.loads(stripped)
                    if str(event.get("event_type")) not in allowed:
                        continue
                    yield trace_event_to_sse(event)
        now = time.monotonic()
        if keepalive_sec > 0 and now - last_keepalive >= keepalive_sec:
            yield ": keepalive\n\n"
            last_keepalive = now
        if poll_interval_sec <= 0:
            break
        time.sleep(poll_interval_sec)


def append_trace_event_sse(trace_path: Path | str, event: TraceEvent) -> str:
    """Append one trace event to disk and return its SSE representation."""

    TraceWriter(trace_path).append(event)
    return trace_event_to_sse(event)
