"""LLM reviewer for authoring benchmark packages.

The reviewer reads only the task prompt and final package artifacts. It does
not read authoring traces, skill loads, or repair history, so the score is
about package quality rather than how the package was produced.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from json import JSONDecodeError
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from labscriptai.runtime.model_adapter import OpenAICompatibleConfig, _strip_json_markdown

from .package_validator import REQUIRED_PACKAGE_FILES
from .tasks import AuthoringTask, load_authoring_tasks

REVIEW_DIMENSIONS = (
    "task_alignment_score",
    "biological_reasonableness_score",
    "liquid_handling_quality_score",
    "safety_control_score",
    "code_quality_score",
)

DEFAULT_LLM_ONLY_BASE_URL = "https://api.vectorengine.ai/v1"

REVIEW_SYSTEM_PROMPT = """You are an independent reviewer of Opentrons protocol-authoring benchmark outputs.
Score the final package against the task prompt, not against the authoring trace.
Do not assume simulation success means experimental correctness.
Return exactly one JSON object with:
- task_alignment_score: integer 1-5
- biological_reasonableness_score: integer 1-5
- liquid_handling_quality_score: integer 1-5
- safety_control_score: integer 1-5
- code_quality_score: integer 1-5
- major_issues: array of concise strings
- notes: concise string, <= 80 words
Scoring guide:
1 = unusable or contradicts task; 2 = major missing elements; 3 = runnable but incomplete/fragile;
4 = mostly correct with minor concerns; 5 = strong, task-faithful, and lab-practical.
Penalize missing controls, wrong volumes, invalid labware/pipettes, contamination risk,
unsafe tip reuse, weak deck/runbook planning, and protocol code that would be hard to audit.
"""


@dataclass(frozen=True)
class ReviewResult:
    task_id: str
    package_dir: str | None
    ok: bool
    scores: dict[str, float]
    major_issues: list[str]
    notes: str
    error: str | None = None

    @property
    def mean_score(self) -> float | None:
        values = [self.scores[key] for key in REVIEW_DIMENSIONS if key in self.scores]
        if not values:
            return None
        return sum(values) / len(values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "package_dir": self.package_dir,
            "ok": self.ok,
            **self.scores,
            "expert_score_mean": self.mean_score,
            "major_issues": self.major_issues,
            "notes": self.notes,
            "error": self.error,
        }


class OpenAICompatibleReviewer:
    def __init__(self, config: OpenAICompatibleConfig, *, opener: Any | None = None) -> None:
        self.config = config
        self.opener = opener or request.urlopen

    def review(self, task: AuthoringTask, package_dir: Path, record: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": build_review_prompt(task, package_dir, record)},
            ],
            "temperature": 0,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        if "api.deepseek.com" in self.config.base_url:
            payload["thinking"] = {"type": "disabled"}
        req = request.Request(
            url=f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        last_error: Exception | None = None
        for attempt in range(self.config.transport_retries):
            try:
                with self.opener(req, timeout=self.config.timeout_sec) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                last_error = None
                break
            except error.HTTPError as exc:
                last_error = exc
                if exc.code not in {408, 429, 500, 502, 503, 504} or attempt + 1 >= self.config.transport_retries:
                    raise
                time.sleep(min(2**attempt, 8))
        if last_error is not None:
            raise last_error
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("reviewer response missing choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            raise ValueError("reviewer response missing message")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            finish_reason = choices[0].get("finish_reason") if isinstance(choices[0], dict) else None
            raise ValueError(f"reviewer response content is empty; finish_reason={finish_reason}")
        parsed = _load_review_json(content)
        if not isinstance(parsed, dict):
            raise ValueError("reviewer JSON must be an object")
        return parsed


def _load_review_json(content: str) -> dict[str, Any]:
    stripped = _strip_json_markdown(content)
    try:
        parsed = json.loads(stripped)
    except JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise
        parsed, _ = json.JSONDecoder().raw_decode(stripped[start:])
    if not isinstance(parsed, dict):
        raise ValueError("reviewer JSON must be an object")
    return parsed


def _read_artifact(path: Path, *, max_chars: int = 12000) -> str:
    if not path.exists():
        return "<missing>"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n<truncated>"


def build_review_prompt(task: AuthoringTask, package_dir: Path, record: dict[str, Any]) -> str:
    artifacts = {
        name: _read_artifact(package_dir / name)
        for name in ("manifest.json", *REQUIRED_PACKAGE_FILES)
        if name != "trace.jsonl"
    }
    simulator_summary = record.get("simulator_summary") or {}
    validation = record.get("validation") or {}
    simulation = record.get("simulation") or {}
    return json.dumps(
        {
            "task": {
                "task_id": task.task_id,
                "difficulty": task.difficulty,
                "prompt": task.prompt,
            },
            "benchmark_observations": {
                "simulation_ok": simulation.get("ok"),
                "validator_ok": validation.get("ok"),
                "critical_failures": validation.get("critical_failures", []),
                "simulator_error_tail": simulator_summary.get("stderr_tail"),
            },
            "package_artifacts": artifacts,
            "instruction": "Score the package quality as JSON using the requested keys.",
        },
        ensure_ascii=False,
    )


def normalize_review(raw: dict[str, Any], *, task_id: str, package_dir: str | None) -> ReviewResult:
    scores: dict[str, float] = {}
    for key in REVIEW_DIMENSIONS:
        value = raw.get(key)
        if not isinstance(value, (int, float)):
            raise ValueError(f"reviewer missing numeric {key}")
        clamped = min(5.0, max(1.0, float(value)))
        scores[key] = clamped
    issues = raw.get("major_issues", [])
    if not isinstance(issues, list):
        issues = [str(issues)]
    notes = raw.get("notes", "")
    return ReviewResult(
        task_id=task_id,
        package_dir=package_dir,
        ok=True,
        scores=scores,
        major_issues=[str(issue) for issue in issues[:8]],
        notes=str(notes),
    )


def _filter_records(
    records: list[dict[str, Any]],
    *,
    limit: int | None = None,
    task_ids: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    filtered = [record for record in records if isinstance(record, dict)]
    if task_ids:
        order = {task_id: index for index, task_id in enumerate(task_ids)}
        selected = [
            record
            for record in filtered
            if str(record.get("task_id", "")) in order
        ]
        selected.sort(key=lambda record: order[str(record.get("task_id", ""))])
        return selected
    if limit is not None:
        return filtered[:limit]
    return filtered


def _fail_fast_http_codes() -> set[int]:
    raw = os.environ.get("REVIEW_FAIL_FAST_HTTP_CODES", "401,403")
    codes: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            codes.add(int(item))
        except ValueError:
            continue
    return codes


def _should_fail_fast_review_error(exc: Exception) -> bool:
    return isinstance(exc, error.HTTPError) and exc.code in _fail_fast_http_codes()


def review_run(
    summary_path: Path | str,
    tasks_path: Path | str,
    output_dir: Path | str,
    *,
    reviewer: Callable[[AuthoringTask, Path, dict[str, Any]], dict[str, Any]],
    limit: int | None = None,
    task_ids: tuple[str, ...] | None = None,
    reviewer_model: str | None = None,
    reviewer_base_url: str | None = None,
    reviewer_api_prefix: str | None = None,
) -> dict[str, Any]:
    summary_path = Path(summary_path)
    output_dir = Path(output_dir)
    task_map = {task.task_id: task for task in load_authoring_tasks(tasks_path)}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    records = summary.get("records", [])
    if not isinstance(records, list):
        raise ValueError("summary records must be a list")
    records = _filter_records(records, limit=limit, task_ids=task_ids)

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for record in records:
        task_id = str(record.get("task_id", ""))
        package_dir_value = record.get("package_dir")
        result_path = output_dir / f"{task_id or 'unknown'}-review.json"
        if result_path.exists():
            try:
                existing_result = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, JSONDecodeError):
                existing_result = None
            if isinstance(existing_result, dict) and existing_result.get("ok") is True:
                results.append(existing_result)
                continue

        if task_id not in task_map or not isinstance(package_dir_value, str):
            result = ReviewResult(
                task_id=task_id,
                package_dir=package_dir_value if isinstance(package_dir_value, str) else None,
                ok=False,
                scores={},
                major_issues=[],
                notes="",
                error="missing task or package_dir",
            )
        else:
            package_dir = Path(package_dir_value)
            try:
                raw = reviewer(task_map[task_id], package_dir, record)
                result = normalize_review(raw, task_id=task_id, package_dir=str(package_dir))
            except Exception as exc:  # noqa: BLE001 - reviewer failures are per-task evidence.
                if _should_fail_fast_review_error(exc):
                    raise
                result = ReviewResult(
                    task_id=task_id,
                    package_dir=str(package_dir),
                    ok=False,
                    scores={},
                    major_issues=[],
                    notes="",
                    error=f"{type(exc).__name__}: {exc}",
                )
        result_dict = result.to_dict()
        results.append(result_dict)
        result_path.write_text(
            json.dumps(result_dict, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    summary_result = summarize_reviews(
        summary_path,
        results,
        reviewer_model=reviewer_model,
        reviewer_base_url=reviewer_base_url,
        reviewer_api_prefix=reviewer_api_prefix,
        panel_task_ids=list(task_ids) if task_ids else None,
    )
    (output_dir / "review-summary.json").write_text(
        json.dumps(summary_result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "review-summary.md").write_text(
        _reviews_to_markdown(summary_result),
        encoding="utf-8",
    )
    return summary_result


def summarize_reviews(
    source_summary: Path | str,
    results: list[dict[str, Any]],
    *,
    reviewer_model: str | None = None,
    reviewer_base_url: str | None = None,
    reviewer_api_prefix: str | None = None,
    panel_task_ids: list[str] | None = None,
) -> dict[str, Any]:
    ok_results = [result for result in results if result.get("ok")]
    means: dict[str, float | None] = {}
    for key in (*REVIEW_DIMENSIONS, "expert_score_mean"):
        values = [float(result[key]) for result in ok_results if isinstance(result.get(key), (int, float))]
        means[key] = (sum(values) / len(values)) if values else None
    payload: dict[str, Any] = {
        "source_summary": str(source_summary),
        "reviewer": {
            "model": reviewer_model,
            "base_url": reviewer_base_url,
            "api_prefix": reviewer_api_prefix,
        },
        "review_count": len(results),
        "review_ok_count": len(ok_results),
        "mean_scores": means,
        "per_task": results,
    }
    if panel_task_ids is not None:
        payload["panel_task_ids"] = panel_task_ids
        payload["panel_task_count"] = len(panel_task_ids)
    return payload


def _fmt_score(value: float | None) -> str:
    return "NA" if value is None else f"{value:.2f}"


def _reviews_to_markdown(result: dict[str, Any]) -> str:
    means = result["mean_scores"]
    lines = [
        "# Authoring Reviewer Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| review_count | {result['review_count']} |",
        f"| review_ok_count | {result['review_ok_count']} |",
        f"| task_alignment_score | {_fmt_score(means['task_alignment_score'])} |",
        f"| biological_reasonableness_score | {_fmt_score(means['biological_reasonableness_score'])} |",
        f"| liquid_handling_quality_score | {_fmt_score(means['liquid_handling_quality_score'])} |",
        f"| safety_control_score | {_fmt_score(means['safety_control_score'])} |",
        f"| code_quality_score | {_fmt_score(means['code_quality_score'])} |",
        f"| expert_score_mean | {_fmt_score(means['expert_score_mean'])} |",
        "",
        "## Per Task",
        "",
        "| Task | Mean | Task Align | Bio | Liquid | Safety | Code | Issues |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["per_task"]:
        issues = "; ".join(row.get("major_issues", []))
        lines.append(
            f"| {row.get('task_id', '')} | {_fmt_score(row.get('expert_score_mean'))} | "
            f"{_fmt_score(row.get('task_alignment_score'))} | "
            f"{_fmt_score(row.get('biological_reasonableness_score'))} | "
            f"{_fmt_score(row.get('liquid_handling_quality_score'))} | "
            f"{_fmt_score(row.get('safety_control_score'))} | "
            f"{_fmt_score(row.get('code_quality_score'))} | {issues} |"
        )
    lines.append("")
    return "\n".join(lines)


def _load_panel_task_ids(panel_path: Path | None) -> tuple[str, ...] | None:
    if panel_path is None:
        return None
    payload = json.loads(panel_path.read_text(encoding="utf-8"))
    raw = payload.get("task_ids", [])
    if not isinstance(raw, list):
        raise ValueError("panel file task_ids must be a list")
    return tuple(str(task_id) for task_id in raw)


def _authoring_review_config(
    *,
    api_prefix: str,
    reviewer_model: str,
) -> OpenAICompatibleConfig:
    default_base_url = (
        DEFAULT_LLM_ONLY_BASE_URL if api_prefix == "LLM_ONLY" else "https://api.deepseek.com"
    )
    return OpenAICompatibleConfig.from_env(
        prefix=api_prefix,
        default_base_url=default_base_url,
        default_model=reviewer_model,
        default_max_tokens=1024,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--tasks", type=Path, default=Path("benchmarks/authoring/tasks.yaml"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reviewer-model", default="deepseek-v4-pro")
    parser.add_argument(
        "--api-prefix",
        choices=("DEEPSEEK", "LLM_ONLY"),
        default="DEEPSEEK",
        help="Environment variable prefix for API credentials (DEEPSEEK_* or LLM_ONLY_*).",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--task-ids",
        default="",
        help="Comma-separated task ids to review (overrides --limit).",
    )
    parser.add_argument(
        "--panel",
        type=Path,
        default=None,
        help="JSON panel manifest with task_ids (e.g. benchmarks/authoring/review_panel_30.json).",
    )
    args = parser.parse_args(argv)

    task_ids: tuple[str, ...] | None = None
    if args.panel is not None:
        task_ids = _load_panel_task_ids(args.panel)
    elif args.task_ids.strip():
        task_ids = tuple(
            task_id.strip()
            for task_id in args.task_ids.split(",")
            if task_id.strip()
        )

    config = _authoring_review_config(
        api_prefix=args.api_prefix,
        reviewer_model=args.reviewer_model,
    )
    if args.reviewer_model:
        config = OpenAICompatibleConfig(
            base_url=config.base_url,
            api_key=config.api_key,
            model=args.reviewer_model,
            timeout_sec=config.timeout_sec,
            max_tokens=config.max_tokens,
            transport_retries=config.transport_retries,
        )
    client = OpenAICompatibleReviewer(config)
    result = review_run(
        args.summary,
        args.tasks,
        args.output_dir,
        reviewer=client.review,
        limit=args.limit if task_ids is None else None,
        task_ids=task_ids,
        reviewer_model=config.model,
        reviewer_base_url=config.base_url,
        reviewer_api_prefix=args.api_prefix,
    )
    print(
        json.dumps(
            {
                "review_count": result["review_count"],
                "review_ok_count": result["review_ok_count"],
                "mean_scores": result["mean_scores"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
