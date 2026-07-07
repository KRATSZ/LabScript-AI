"""Lightweight task-aware KB context for unified authoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labscriptai.authoring.protocol_rag import search_protocol_library
from labscriptai.benchmark.tasks import AuthoringTask


TASK_TYPE_SKILLS = {
    "dilution": "dilution",
    "serial_dilution": "serial_dilution",
    "plate_transfer": "plate_transfer",
    "normalization": "normalization",
    "pcr_setup": "pcr_setup",
    "module_usage": "module_usage",
}

TASK_TYPE_QUERIES = {
    "dilution": ("dilution",),
    "serial_dilution": ("serial dilution",),
    "plate_transfer": ("transfer",),
    "normalization": ("normalization",),
    "pcr_setup": ("pcr", "qpcr"),
}


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return clipped or text[:limit].rstrip()


@dataclass(frozen=True)
class KBContext:
    context_mode: str
    task_types: tuple[str, ...]
    skill_summaries: tuple[dict[str, str], ...]
    protocol_hits: tuple[dict[str, str], ...]
    memory_hits: tuple[dict[str, str], ...]
    legacy_type: str | None = None
    recommended_skills: tuple[str, ...] = ()
    task_obligations: dict[str, Any] | None = None

    @property
    def token_estimate(self) -> int:
        text = json.dumps(self.to_prompt_payload(), ensure_ascii=False)
        return max(1, len(text) // 4)

    def to_prompt_payload(self) -> dict[str, Any]:
        if self.context_mode == "compact_v2":
            return {
                "context_mode": self.context_mode,
                "legacy_type": self.legacy_type,
                "task_types": list(self.task_types),
                "recommended_skills": list(self.recommended_skills),
                "task_obligations": self.task_obligations or {},
                "failure_patterns": list(self.memory_hits[:1]),
                "usage_rule": (
                    "Use this as routing and obligations only. Load recommended skills only if needed. "
                    "Do not add extra samples or controls beyond task_obligations."
                ),
            }
        usage_rule = (
            "Use as a short checklist only. Follow the task prompt if it conflicts."
            if self.context_mode == "compact"
            else (
                "Use this short KB as guardrails only. Do not copy reference code blindly. "
                "Prefer the task prompt when KB conflicts with task-specific requirements."
            )
        )
        return {
            "context_mode": self.context_mode,
            "task_types": list(self.task_types),
            "usage_rule": usage_rule,
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
    context_mode: str = "full",
) -> KBContext:
    if context_mode not in {"full", "compact", "compact_v2"}:
        raise ValueError("context_mode must be one of: full, compact, compact_v2")
    repo_root = repo_root or Path(__file__).resolve().parents[3]
    skills_dir = skills_dir or Path(__file__).resolve().parent / "skills"
    failure_patterns_path = failure_patterns_path or Path(__file__).resolve().parent / "failure_patterns.json"
    if context_mode == "compact_v2":
        task_types = classify_task(task)
        memory_hits = tuple(
            _failure_pattern_hits(
                task_types,
                failure_patterns_path,
                max_items=1,
                compact=True,
            )
        ) or (_fallback_failure_pattern(task_types[0]),)
        return KBContext(
            context_mode=context_mode,
            task_types=task_types,
            skill_summaries=(),
            protocol_hits=(),
            memory_hits=memory_hits,
            legacy_type=task.legacy_type,
            recommended_skills=tuple(TASK_TYPE_SKILLS.get(task_type, task_type) for task_type in task_types),
            task_obligations=_task_obligations(task),
        )
    if context_mode == "compact":
        max_items = 1
    task_types = classify_task(task)
    skill_summaries = tuple(
        _skill_summary(
            task_type,
            skills_dir / f"{TASK_TYPE_SKILLS[task_type]}.md",
            compact=context_mode == "compact",
        )
        for task_type in task_types
        if task_type in TASK_TYPE_SKILLS
    )[:max_items]
    protocol_hits = tuple(
        _search_protocols(
            task_types,
            repo_root,
            max_items=max_items,
            compact=context_mode == "compact",
        )
    )
    memory_hits = tuple(
        _failure_pattern_hits(
            task_types,
            failure_patterns_path,
            max_items=max_items,
            compact=context_mode == "compact",
        )
    )
    return KBContext(context_mode, task_types, skill_summaries, protocol_hits, memory_hits)


def classify_task(task: AuthoringTask) -> tuple[str, ...]:
    legacy_type = (task.legacy_type or "").lower()
    routed = _route_legacy_type(legacy_type)
    if routed:
        return routed
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


def _route_legacy_type(legacy_type: str) -> tuple[str, ...]:
    if not legacy_type:
        return ()
    if legacy_type == "reservoir_dead_volume":
        return ("plate_transfer",)
    if legacy_type in {"module_state_pause", "module_coordination"}:
        return ("module_usage",)
    if legacy_type.startswith("pcr_setup") or legacy_type.startswith("qpcr"):
        return ("pcr_setup",)
    if legacy_type == "serial_dilution" or "serial_dilution" in legacy_type:
        return ("serial_dilution",)
    if "normalization" in legacy_type:
        return ("normalization",)
    if legacy_type in {"controls_plate_layout", "conditional_controls"}:
        return ("plate_transfer",)
    return ()


def _task_obligations(task: AuthoringTask) -> dict[str, Any]:
    obligations: dict[str, Any] = {"task_id": task.task_id}
    if task.spec.default_samples is not None:
        obligations["default_samples"] = task.spec.default_samples
    reagents: list[dict[str, Any]] = []
    for reagent in task.spec.reagents:
        item: dict[str, Any] = {"name": reagent.name}
        if reagent.volume_per_sample_uL is not None:
            item["per_sample_uL"] = reagent.volume_per_sample_uL
            if task.spec.default_samples is not None:
                item["expected_total_uL"] = task.spec.default_samples * reagent.volume_per_sample_uL
        reagents.append(item)
    if reagents:
        obligations["reagents"] = reagents
    if task.spec.controls:
        obligations["controls"] = task.spec.controls
    if task.spec.expected_risk_flags:
        obligations["risk_flags"] = list(task.spec.expected_risk_flags)
    module_required = _module_required(task)
    if module_required:
        obligations["module_required"] = module_required
    return obligations


def _module_required(task: AuthoringTask) -> str | None:
    text = f"{task.legacy_type or ''} {task.prompt}".lower()
    if "thermocycler, magnetic, or temperature" in text:
        return "module"
    if "thermocycler" in text:
        return "thermocycler"
    if "magnetic" in text or "magnet" in text:
        return "magnetic_module"
    if "temperature module" in text or "cold block" in text:
        return "temperature_module"
    if "module" in text:
        return "module"
    return None


def _fallback_failure_pattern(task_type: str) -> dict[str, str]:
    if task_type == "module_usage":
        return {
            "task_type": task_type,
            "common_failure": "Module task describes a module but omits executable pause/lid/magnet/temperature state control.",
            "fix": "Declare the module state and include pause/open_lid/cool/engage/disengage as applicable.",
        }
    return {
        "task_type": task_type,
        "common_failure": "Generated package drifts from sample, reagent, control, or tip counts in the task.",
        "fix": "Use task_obligations as the counting source of truth.",
    }


def _skill_summary(task_type: str, path: Path, *, compact: bool = False) -> dict[str, str]:
    if not path.exists():
        return {"task_type": task_type, "summary": "No task-specific skill file found."}
    lines = [
        line.strip("- ").strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if compact:
        return {"task_type": task_type, "summary": _clip(" ".join(lines[:2]), 140)}
    return {"task_type": task_type, "summary": _clip(" ".join(lines[:8]), 900)}


def _failure_pattern_hits(
    task_types: tuple[str, ...],
    failure_patterns_path: Path,
    *,
    max_items: int,
    compact: bool = False,
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
    for task_type in task_types:
        for item in payload:
            if not isinstance(item, dict) or item.get("task_type") != task_type:
                continue
            hit = {
                "task_type": str(item.get("task_type", "")),
                "common_failure": _clip(str(item.get("common_failure", "")), 100),
                "fix": _clip(str(item.get("fix", "")), 110),
            }
            if not compact:
                hit.update(
                    {
                        "preferred_labware": str(item.get("preferred_labware", "")),
                        "preferred_pipette": str(item.get("preferred_pipette", "")),
                    }
                )
            hits.append(hit)
            if len(hits) >= max_items:
                return hits
    return hits


def _search_protocols(
    task_types: tuple[str, ...],
    repo_root: Path,
    *,
    max_items: int,
    compact: bool = False,
) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for task_type in task_types:
        for query in TASK_TYPE_QUERIES.get(task_type, ()):
            try:
                raw_hits = search_protocol_library(query, repo_root=repo_root, limit=max_items)
            except (FileNotFoundError, OSError):
                return []
            for hit in raw_hits:
                key = str(hit.get("path") or hit.get("name") or "")
                if not key or key in seen:
                    continue
                seen.add(key)
                title = _clip(str(hit.get("title") or hit.get("name") or ""), 120)
                protocol_hit = {
                    "task_type": task_type,
                    "title": title,
                    "path": _clip(key, 140),
                }
                if compact:
                    protocol_hit["why_relevant"] = f"Closest {task_type} reference; API sanity check only."
                else:
                    protocol_hit.update(
                        {
                            "query": query,
                            "summary": str(hit.get("description") or "")[:500],
                        }
                    )
                hits.append(protocol_hit)
                if len(hits) >= max_items:
                    return hits
    return hits
