"""Lightweight loader for the frozen authoring benchmark task manifest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskReagentSpec:
    name: str
    volume_per_sample_uL: float | None = None
    source: str | None = None


@dataclass(frozen=True)
class TaskSpec:
    default_samples: int | None = None
    reagents: tuple[TaskReagentSpec, ...] = ()
    controls: dict[str, Any] | None = None
    expected_risk_flags: tuple[str, ...] = ()


DIFFICULTY_STRATA: tuple[str, ...] = ("Easy", "Medium", "Hard", "Expert")

# Frozen 30-task panel for multi-reviewer cross-check (proportional to full 90-task mix).
REVIEW_PANEL_COUNTS: dict[str, int] = {
    "Easy": 5,
    "Medium": 13,
    "Hard": 10,
    "Expert": 2,
}


@dataclass(frozen=True)
class AuthoringTask:
    task_id: str
    source: str
    difficulty: str
    holdout: bool
    output_contract: str
    prompt: str
    legacy_type: str | None = None
    spec: TaskSpec = TaskSpec()
    off_platform_handoff: tuple[str, ...] = ()

    @property
    def is_new(self) -> bool:
        return self.source == "new_35"


def load_authoring_tasks(path: Path | str) -> tuple[AuthoringTask, ...]:
    """Load the subset of tasks.yaml fields needed by smoke/benchmark runners.

    The project intentionally keeps runtime dependencies empty. This parser is
    narrow by design and supports the current frozen manifest structure.
    """

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    tasks: list[AuthoringTask] = []
    current: dict[str, object] | None = None
    prompt_lines: list[str] = []
    in_prompt = False
    in_expected_risk_flags = False
    in_off_platform_handoff = False
    in_reagents = False
    in_controls = False
    current_reagent: dict[str, object] | None = None
    in_tasks = False

    def flush_reagent() -> None:
        nonlocal current_reagent
        if current is None or current_reagent is None:
            return
        name = current_reagent.get("name")
        if isinstance(name, str):
            current["reagents"] = (
                *current.get("reagents", ()),
                TaskReagentSpec(
                    name=name,
                    volume_per_sample_uL=current_reagent.get("volume_per_sample_uL")
                    if isinstance(current_reagent.get("volume_per_sample_uL"), (int, float))
                    else None,
                    source=current_reagent.get("source")
                    if isinstance(current_reagent.get("source"), str)
                    else None,
                ),
            )
        current_reagent = None

    def flush() -> None:
        nonlocal current, prompt_lines, in_prompt, in_expected_risk_flags, in_off_platform_handoff, in_reagents, in_controls
        if current is None:
            return
        flush_reagent()
        task_id = current.get("id")
        source = current.get("source")
        difficulty = current.get("difficulty")
        holdout = current.get("holdout")
        output_contract = current.get("output_contract", "")
        if (
            not isinstance(task_id, str)
            or not isinstance(source, str)
            or not isinstance(difficulty, str)
            or not isinstance(output_contract, str)
        ):
            raise ValueError(f"task manifest entry is missing required fields: {current!r}")
        if not isinstance(holdout, bool):
            raise ValueError(f"task {task_id} has invalid holdout value")
        default_samples = current.get("default_samples")
        if default_samples is not None and not isinstance(default_samples, int):
            raise ValueError(f"task {task_id} has invalid default_samples value")
        expected_risk_flags = current.get("expected_risk_flags", ())
        if not isinstance(expected_risk_flags, tuple):
            raise ValueError(f"task {task_id} has invalid expected_risk_flags value")
        reagents = current.get("reagents", ())
        if not isinstance(reagents, tuple):
            raise ValueError(f"task {task_id} has invalid reagents value")
        controls = current.get("controls")
        if controls is not None and not isinstance(controls, dict):
            raise ValueError(f"task {task_id} has invalid controls value")
        off_platform_handoff = current.get("off_platform_handoff", ())
        if not isinstance(off_platform_handoff, tuple):
            raise ValueError(f"task {task_id} has invalid off_platform_handoff value")
        tasks.append(
            AuthoringTask(
                task_id=task_id,
                source=source,
                difficulty=difficulty,
                holdout=holdout,
                output_contract=output_contract,
                prompt="\n".join(prompt_lines).strip(),
                legacy_type=current.get("legacy_type")
                if isinstance(current.get("legacy_type"), str)
                else None,
                spec=TaskSpec(
                    default_samples=default_samples,
                    reagents=reagents,
                    controls=controls,
                    expected_risk_flags=expected_risk_flags,
                ),
                off_platform_handoff=off_platform_handoff,
            )
        )
        current = None
        prompt_lines = []
        in_prompt = False
        in_expected_risk_flags = False
        in_off_platform_handoff = False
        in_reagents = False
        in_controls = False

    for line in lines:
        if line == "tasks:":
            in_tasks = True
            continue
        if not in_tasks:
            continue
        if line.startswith("  - id: "):
            flush()
            current = {"id": line.split(":", 1)[1].strip()}
            continue
        if current is None:
            continue
        if line.startswith("    prompt: |"):
            flush_reagent()
            in_prompt = True
            in_expected_risk_flags = False
            in_off_platform_handoff = False
            in_reagents = False
            in_controls = False
            prompt_lines = []
            continue
        if in_prompt:
            if line == "":
                prompt_lines.append("")
                continue
            if line.startswith("      "):
                prompt_lines.append(line[6:])
                continue
            in_prompt = False
        if line.startswith("    source: "):
            current["source"] = line.split(":", 1)[1].strip()
        elif line.startswith("    difficulty: "):
            current["difficulty"] = line.split(":", 1)[1].strip()
        elif line.startswith("    holdout: "):
            value = line.split(":", 1)[1].strip()
            if value not in {"true", "false"}:
                raise ValueError(f"invalid holdout value for task {current.get('id')}: {value}")
            current["holdout"] = value == "true"
        elif line.startswith("    output_contract: "):
            current["output_contract"] = line.split(":", 1)[1].strip()
        elif line.startswith("    legacy_type: "):
            current["legacy_type"] = _strip_yaml_scalar(line.split(":", 1)[1].strip())
        elif line.startswith("    off_platform_handoff: ["):
            current["off_platform_handoff"] = _parse_inline_list(line.split(":", 1)[1].strip())
            in_off_platform_handoff = False
        elif line.startswith("    off_platform_handoff:"):
            current["off_platform_handoff"] = ()
            in_off_platform_handoff = True
        elif line.startswith("      default_samples: "):
            current["default_samples"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("      reagents:"):
            flush_reagent()
            in_reagents = True
            in_controls = False
        elif line.startswith("      controls:"):
            flush_reagent()
            in_reagents = False
            in_controls = True
            current["controls"] = {}
        elif in_controls and line.startswith("        ") and ": " in line:
            key, raw_value = line.strip().split(":", 1)
            controls = current.setdefault("controls", {})
            if isinstance(controls, dict):
                controls[key] = _parse_control_value(raw_value.strip())
        elif in_reagents and line.startswith("        - name: "):
            flush_reagent()
            current_reagent = {"name": _strip_yaml_scalar(line.split(":", 1)[1].strip())}
        elif in_reagents and current_reagent is not None and line.startswith(
            "          volume_per_sample_uL: "
        ):
            raw = line.split(":", 1)[1].strip()
            current_reagent["volume_per_sample_uL"] = float(raw) if "." in raw else int(raw)
        elif in_reagents and current_reagent is not None and line.startswith("          source: "):
            current_reagent["source"] = _strip_yaml_scalar(line.split(":", 1)[1].strip())
        elif line.startswith("      expected_risk_flags:"):
            flush_reagent()
            in_reagents = False
            in_controls = False
            current["expected_risk_flags"] = ()
            in_expected_risk_flags = True
        elif in_expected_risk_flags and line.startswith("        - "):
            value = _strip_yaml_scalar(line.split("-", 1)[1].strip())
            current["expected_risk_flags"] = (*current.get("expected_risk_flags", ()), value)
        elif in_off_platform_handoff and line.startswith("      - "):
            value = _strip_yaml_scalar(line.split("-", 1)[1].strip())
            current["off_platform_handoff"] = (*current.get("off_platform_handoff", ()), value)
        elif line.startswith("    ") and not line.startswith("      "):
            flush_reagent()
            in_reagents = False
            in_controls = False
            in_expected_risk_flags = False
            in_off_platform_handoff = False

    flush()
    if not tasks:
        raise ValueError(f"no tasks loaded from {path}")
    return tuple(tasks)


def _strip_yaml_scalar(value: str) -> str:
    if value in {"none", "null"}:
        return value
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_inline_list(value: str) -> tuple[str, ...]:
    if not value.startswith("[") or not value.endswith("]"):
        return ()
    inner = value[1:-1].strip()
    if not inner:
        return ()
    return tuple(_strip_yaml_scalar(item.strip()) for item in inner.split(","))


def _parse_control_value(value: str) -> object:
    stripped = _strip_yaml_scalar(value)
    if stripped in {"none", "null"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        return list(_parse_inline_list(value))
    return stripped


def select_stratified_tasks(
    tasks: tuple[AuthoringTask, ...],
    *,
    per_level: int = 1,
    holdout_only: bool = True,
    prefer_new: bool = True,
) -> tuple[AuthoringTask, ...]:
    """Select a stable small sample across difficulty strata (Easy/Medium/Hard/Expert).

    ``per_level`` is retained for CLI compatibility; it means *per difficulty stratum*.
    When ``holdout_only`` is true, a stratum with no hold-out tasks contributes nothing
    (e.g. there are currently no Expert hold-outs in the frozen manifest).
    """

    if per_level < 1:
        raise ValueError("per_level must be >= 1")
    selected: list[AuthoringTask] = []
    for difficulty in DIFFICULTY_STRATA:
        candidates = [
            task
            for task in tasks
            if task.difficulty == difficulty and (task.holdout or not holdout_only)
        ]
        if prefer_new:
            candidates.sort(key=lambda task: (not task.is_new, task.task_id))
        else:
            candidates.sort(key=lambda task: task.task_id)
        selected.extend(candidates[:per_level])
    return tuple(selected)


def select_review_panel_task_ids(
    tasks: tuple[AuthoringTask, ...],
    *,
    counts: dict[str, int] | None = None,
) -> tuple[str, ...]:
    """Pick a stable stratified panel (~30 tasks) for secondary LLM reviewers."""

    panel_counts = counts or REVIEW_PANEL_COUNTS
    selected: list[str] = []
    for difficulty in DIFFICULTY_STRATA:
        target = panel_counts.get(difficulty, 0)
        if target < 1:
            continue
        pool = sorted(
            (task for task in tasks if task.difficulty == difficulty),
            key=lambda task: task.task_id,
        )
        if not pool:
            continue
        if len(pool) <= target:
            chosen = pool
        elif target == 1:
            chosen = [pool[0]]
        else:
            chosen = [
                pool[int(round(index * (len(pool) - 1) / (target - 1)))]
                for index in range(target)
            ]
        selected.extend(task.task_id for task in chosen)
    return tuple(selected)
