"""Lightweight task-aware KB context for unified authoring."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labscriptai.benchmark.tasks import AuthoringTask


TASK_TYPE_SKILLS = {
    "dilution": "dilution",
    "serial_dilution": "serial_dilution",
    "plate_transfer": "plate_transfer",
    "normalization": "normalization",
    "pcr_setup": "pcr_setup",
}

TASK_TYPE_QUERIES = {
    "dilution": ("dilution buffer plate transfer opentrons",),
    "serial_dilution": ("serial dilution plate opentrons",),
    "plate_transfer": ("96 well plate transfer opentrons",),
    "normalization": ("DNA normalization concentration volume opentrons",),
    "pcr_setup": ("PCR setup master mix plate opentrons",),
}


@dataclass(frozen=True)
class KBContext:
    task_types: tuple[str, ...]
    skill_summaries: tuple[dict[str, str], ...]
    protocol_hits: tuple[dict[str, str], ...]
    memory_hits: tuple[dict[str, str], ...]

    @property
    def token_estimate(self) -> int:
        text = json.dumps(self.to_prompt_payload(), ensure_ascii=False)
        return max(1, len(text) // 4)

    def to_prompt_payload(self) -> dict[str, Any]:
        return {
            "task_types": list(self.task_types),
            "usage_rule": (
                "Use this short KB as guardrails only. Do not copy reference code blindly. "
                "Prefer the task prompt when KB conflicts with task-specific requirements."
            ),
            "skill_summaries": list(self.skill_summaries),
            "protocol_reference_summaries": list(self.protocol_hits),
            "failure_patterns": list(self.memory_hits),
        }

    def to_stats(self) -> dict[str, int]:
        return {
            "protocol_hits": len(self.protocol_hits),
            "memory_hits": len(self.memory_hits),
            "kb_context_tokens_estimate": self.token_estimate,
        }


def build_kb_context(
    task: AuthoringTask,
    *,
    skills_dir: Path | None = None,
    failure_patterns_path: Path | None = None,
    repo_root: Path | None = None,
    max_items: int = 3,
) -> KBContext:
    repo_root = repo_root or Path(__file__).resolve().parents[3]
    skills_dir = skills_dir or Path(__file__).resolve().parent / "skills"
    failure_patterns_path = failure_patterns_path or Path(__file__).resolve().parent / "failure_patterns.json"
    task_types = classify_task(task)
    skill_summaries = tuple(
        _skill_summary(task_type, skills_dir / f"{TASK_TYPE_SKILLS[task_type]}.md")
        for task_type in task_types
        if task_type in TASK_TYPE_SKILLS
    )[:max_items]
    protocol_hits = tuple(_search_protocols(task_types, repo_root, max_items=max_items))
    memory_hits = tuple(_failure_pattern_hits(task_types, failure_patterns_path, max_items=max_items))
    return KBContext(task_types, skill_summaries, protocol_hits, memory_hits)


def classify_task(task: AuthoringTask) -> tuple[str, ...]:
    text = f"{task.task_id} {task.prompt}".lower()
    detected: list[str] = []
    if "serial dilution" in text or ("serial" in text and "dilution" in text):
        detected.append("serial_dilution")
    if "dilution" in text and "serial_dilution" not in detected:
        detected.append("dilution")
    if "normalization" in text or "normalize" in text:
        detected.append("normalization")
    if "pcr" in text or "qpcr" in text or "master mix" in text:
        detected.append("pcr_setup")
    if "transfer" in text or "plate" in text:
        detected.append("plate_transfer")
    return tuple(detected[:3] or ("plate_transfer",))


def _skill_summary(task_type: str, path: Path) -> dict[str, str]:
    if not path.exists():
        return {"task_type": task_type, "summary": "No task-specific skill file found."}
    lines = [
        line.strip("- ").strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return {"task_type": task_type, "summary": " ".join(lines[:8])[:900]}


def _failure_pattern_hits(
    task_types: tuple[str, ...],
    failure_patterns_path: Path,
    *,
    max_items: int,
) -> list[dict[str, str]]:
    if not failure_patterns_path.exists():
        return []
    try:
        payload = json.loads(failure_patterns_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    hits: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict) or item.get("task_type") not in task_types:
            continue
        hits.append(
            {
                "task_type": str(item.get("task_type", "")),
                "common_failure": str(item.get("common_failure", "")),
                "fix": str(item.get("fix", "")),
                "preferred_labware": str(item.get("preferred_labware", "")),
                "preferred_pipette": str(item.get("preferred_pipette", "")),
            }
        )
        if len(hits) >= max_items:
            break
    return hits


def _search_protocols(
    task_types: tuple[str, ...],
    repo_root: Path,
    *,
    max_items: int,
) -> list[dict[str, str]]:
    script = repo_root / "skills" / "opentrons-protocol-library" / "scripts" / "search_protocols.py"
    if not script.exists():
        return []
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for task_type in task_types:
        for query in TASK_TYPE_QUERIES.get(task_type, ()):
            for hit in _run_protocol_search(script, repo_root, query):
                key = str(hit.get("path") or hit.get("name") or "")
                if not key or key in seen:
                    continue
                seen.add(key)
                hits.append(
                    {
                        "task_type": task_type,
                        "query": query,
                        "title": str(hit.get("title") or hit.get("name") or "")[:160],
                        "path": key[:160],
                        "summary": str(hit.get("description") or "")[:500],
                    }
                )
                if len(hits) >= max_items:
                    return hits
    return hits


def _run_protocol_search(script: Path, repo_root: Path, query: str) -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["uv", "run", "python", str(script), "search", query],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []
