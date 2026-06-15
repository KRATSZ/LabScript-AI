#!/usr/bin/env python3
"""Build OpentronsAI chat prompts aligned to the py-only LLM-only baseline.

Each prompt is a flattened message: PY_ONLY_AUTHORING_SYSTEM_PROMPT + task text.
Outputs a human-readable markdown doc and a machine-readable JSONL manifest for
browser collection (phase 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from labscriptai.benchmark.authoring_pilot import PY_ONLY_AUTHORING_SYSTEM_PROMPT, _prompt_hash
from labscriptai.benchmark.tasks import AuthoringTask, load_authoring_tasks


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "benchmarks/authoring/tasks.yaml"
DEFAULT_OUT = ROOT / "runs/authoring90/opentrons_ai_v1"


def build_full_prompt(task: AuthoringTask) -> str:
    """Flatten system + user into one chat message (OpentronsAI has no system role)."""
    prefix = PY_ONLY_AUTHORING_SYSTEM_PROMPT.strip()
    body = task.prompt.rstrip()
    return f"{prefix}\n\nTask (difficulty: {task.difficulty}):\n{body}\n"


def build_prompt_record(task: AuthoringTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "holdout": task.holdout,
        "prompt_hash": _prompt_hash(task.prompt),
        "full_prompt": build_full_prompt(task),
    }


def render_prompt_doc(records: list[dict[str, Any]], *, tasks_path: Path, generated_at: str) -> str:
    lines = [
        "# OpentronsAI prompt document (Table 1 baseline)",
        "",
        "Paste each **Full prompt** block into a **new** chat at "
        "[OpentronsAI](https://ai.opentrons.com/#/chat).",
        "",
        "## Contract",
        "",
        "- **Alignment**: flattened `PY_ONLY_AUTHORING_SYSTEM_PROMPT` + task text, "
        "matching the py-only LLM-only / native-agent baselines.",
        "- **`prompt_hash`**: SHA-256 of `task.prompt` only (same as other benchmark rows).",
        "- **Output expected**: `protocol.py` only; harness derives sidecars post-hoc.",
        "- **Do not** add manifest/setup-card requirements or LabscriptAI scaffold text.",
        "",
        f"- **Tasks manifest**: `{tasks_path}`",
        f"- **Generated at**: {generated_at}",
        f"- **Task count**: {len(records)}",
        "",
        "---",
        "",
    ]
    for record in records:
        task_id = record["task_id"]
        lines.extend(
            [
                f"## {task_id}",
                "",
                f"- **Difficulty**: {record['difficulty']}",
                f"- **Holdout**: {record['holdout']}",
                f"- **prompt_hash**: `{record['prompt_hash']}`",
                "",
                "### Full prompt",
                "",
                "```text",
                record["full_prompt"].rstrip(),
                "```",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    records: list[dict[str, Any]],
    *,
    out_dir: Path,
    tasks_path: Path,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()

    jsonl_path = out_dir / "prompts.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    meta = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "tasks_path": str(tasks_path),
        "task_count": len(records),
        "prompt_format": "flattened_py_only",
        "system_prompt_source": "labscriptai.benchmark.authoring_pilot.PY_ONLY_AUTHORING_SYSTEM_PROMPT",
        "prompt_hash_scope": "task.prompt only (excludes system prefix)",
        "collection_target": "https://ai.opentrons.com/#/chat",
    }
    (out_dir / "prompt_manifest.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    doc_path = out_dir / "prompt_doc.md"
    doc_path.write_text(
        render_prompt_doc(records, tasks_path=tasks_path, generated_at=generated_at),
        encoding="utf-8",
    )
    return doc_path, jsonl_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks",
        type=Path,
        default=DEFAULT_TASKS,
        help="Authoring task manifest (default: benchmarks/authoring/tasks.yaml)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory (default: runs/authoring90/opentrons_ai_v1)",
    )
    args = parser.parse_args(argv)

    tasks_path = args.tasks.resolve()
    tasks = load_authoring_tasks(tasks_path)
    if not tasks:
        print(f"no tasks loaded from {tasks_path}", file=sys.stderr)
        return 1

    records = [build_prompt_record(task) for task in tasks]
    doc_path, jsonl_path = write_outputs(records, out_dir=args.out_dir.resolve(), tasks_path=tasks_path)
    print(f"Wrote {len(records)} prompts to {jsonl_path}")
    print(f"Wrote {doc_path}")
    print(f"Wrote {args.out_dir.resolve() / 'prompt_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
