"""Markdown-backed runtime memory for failure and recovery notes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class MemoryHit:
    path: Path
    title: str
    score: int
    preview: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "title": self.title,
            "score": self.score,
            "preview": self.preview,
        }


def append_memory_note(
    memory_dir: Path,
    *,
    title: str,
    body: str,
    tags: tuple[str, ...] = (),
    metadata: Mapping[str, Any] | None = None,
) -> Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _utc_now()
    slug = _slug(title) or "runtime-note"
    path = memory_dir / f"{timestamp.replace(':', '').replace('-', '')}-{slug}.md"
    frontmatter = [
        "---",
        f"title: {title}",
        f"created_at: {timestamp}",
        f"tags: {', '.join(tags)}",
    ]
    for key, value in sorted(dict(metadata or {}).items()):
        frontmatter.append(f"{key}: {value}")
    frontmatter.extend(["---", "", body.strip(), ""])
    path.write_text("\n".join(frontmatter), encoding="utf-8")
    return path


def remember_shadow_record(memory_dir: Path, record: Mapping[str, Any]) -> Path:
    title = f"{record.get('error_category', 'runtime')} recovery: {record.get('action_type', 'unknown')}"
    body = "\n".join(
        [
            f"- case_id: {record.get('case_id', '')}",
            f"- run_id: {record.get('run_id', '')}",
            f"- expected_policy: {record.get('expected_policy', '')}",
            f"- gatekeeper_status: {record.get('gatekeeper_status', '')}",
            f"- passed: {record.get('passed', False)}",
            f"- reasons: {', '.join(str(item) for item in record.get('reasons', []))}",
        ]
    )
    return append_memory_note(
        memory_dir,
        title=title,
        body=body,
        tags=("runtime", "recovery", str(record.get("error_category", "unknown"))),
        metadata={"case_id": record.get("case_id", ""), "run_id": record.get("run_id", "")},
    )


def search_memory(memory_dir: Path, query: str, *, limit: int = 5) -> list[MemoryHit]:
    if not memory_dir.exists():
        return []
    query_terms = _terms(query)
    hits: list[MemoryHit] = []
    for path in sorted(memory_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        terms = _terms(text)
        score = sum(1 for term in query_terms if term in terms)
        if score <= 0:
            continue
        hits.append(
            MemoryHit(
                path=path,
                title=_title(text) or path.stem,
                score=score,
                preview=_preview(text, query_terms),
            )
        )
    hits.sort(key=lambda hit: (-hit.score, hit.path.name))
    return hits[:limit]


def count_branch_outcomes(
    memory_dir: Path,
    branch: str,
    error_leaf: str | None = None,
) -> dict[str, int]:
    if not memory_dir.exists():
        return {"total": 0, "fails": 0}
    total = 0
    fails = 0
    target_branch = str(branch)
    target_leaf = str(error_leaf or "")
    for path in sorted(memory_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        metadata = _frontmatter(text)
        if metadata.get("branch") != target_branch:
            continue
        if target_leaf and metadata.get("error_leaf") != target_leaf:
            continue
        status = str(metadata.get("status") or "").strip().lower()
        if not status:
            continue
        total += 1
        if status in {"fail", "failed", "blocked", "escalated"}:
            fails += 1
    return {"total": total, "fails": fails}


def _terms(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_\-\u4e00-\u9fff]+", text)}


def _slug(text: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return "-".join(tokens[:8])


def _title(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip()
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _preview(text: str, query_terms: set[str]) -> str:
    for line in text.splitlines():
        normalized = line.lower()
        if any(term in normalized for term in query_terms):
            return line.strip()[:240]
    return text.strip().replace("\n", " ")[:240]


def _frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    metadata: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
