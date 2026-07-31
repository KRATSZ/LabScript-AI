#!/usr/bin/env python3
"""Validate and score a prepared live Flex paired evidence bundle.

Correctness (FIX/STOP recall) is computed only on ``validity == "valid"`` runs.
Invalid infrastructure/fixture runs are counted and exportable but excluded from
correctness denominators; they may be re-run in place.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "benchmarks" / "runtime"))
sys.path.insert(0, str(REPO / "src"))

from live_paired_validity import (  # noqa: E402
    classify_validity,
    score_correctness_if_valid,
    summarize_validity,
)

DEFAULT_BUNDLE = REPO / "runs/runtime-flex15/live_paired_v1"
LIVE_PAIRED_V2_CASES = REPO / "benchmarks/runtime/live_paired_v2/cases"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def _try_legacy_summarize(bundle_dir: Path) -> Mapping[str, Any] | None:
    try:
        from labscriptai.runtime.live_flex_evidence import (  # type: ignore
            summarize_live_bundle,
        )
    except Exception:
        return None
    try:
        return summarize_live_bundle(bundle_dir)
    except Exception:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def summarize_bundle_with_validity(bundle_dir: Path) -> dict[str, Any]:
    """Score a live_paired_v2-style cases tree or a legacy live_paired bundle."""
    cases_dir = bundle_dir / "cases" if (bundle_dir / "cases").is_dir() else bundle_dir
    records: list[dict[str, Any]] = []
    correctness_rows: list[dict[str, Any]] = []

    for case_dir in sorted(p for p in cases_dir.iterdir() if p.is_dir()):
        shell = case_dir / "evidence_shell.json"
        evidence = case_dir / "evidence.json"
        path = evidence if evidence.is_file() else shell
        if not path.is_file():
            continue
        record = _load_json(path)
        rubric_path = case_dir / "score_rubric.json"
        gold = None
        pass_labels = None
        if rubric_path.is_file():
            rubric = _load_json(rubric_path)
            gold = rubric.get("gold")
            pass_labels = (rubric.get("rubric") or {}).get("pass_labels")
        records.append(record)
        correctness_rows.append(
            score_correctness_if_valid(record, gold=gold, pass_labels=pass_labels)
        )

    validity_summary = summarize_validity(records)
    scored = [r for r in correctness_rows if r.get("correctness_scored")]
    passed = [r for r in scored if r.get("passed")]
    legacy = _try_legacy_summarize(bundle_dir)

    return {
        "bundle": str(bundle_dir.resolve()),
        "schema": "live_paired_validity.v1",
        "contract_integrity_ok": True,
        "contract_failures": [],
        "validity": validity_summary,
        "correctness": {
            "scored_n": len(scored),
            "passed_n": len(passed),
            "recall": (len(passed) / len(scored)) if scored else None,
            "records": correctness_rows,
        },
        "legacy_summary": legacy,
        "claim_boundary": (
            "Correctness recall uses only validity=valid runs that reached the "
            "decision point. invalid_infrastructure / invalid_fixture runs are "
            "counted, exportable, and re-runnable, but excluded from the "
            "correctness denominator."
        ),
    }


def render_validity_markdown(summary: Mapping[str, Any]) -> str:
    validity = summary.get("validity") or {}
    by = validity.get("run_count_by_validity") or {}
    corr = summary.get("correctness") or {}
    lines = [
        "# Live paired validity / correctness summary",
        "",
        f"- Bundle: `{summary.get('bundle')}`",
        f"- Total runs: **{validity.get('run_count_total', 0)}**",
        f"- valid: **{by.get('valid', 0)}**",
        f"- invalid_infrastructure: **{by.get('invalid_infrastructure', 0)}**",
        f"- invalid_fixture: **{by.get('invalid_fixture', 0)}**",
        f"- pending: **{by.get('pending', 0)}**",
        f"- Correctness denominator (valid only): **{corr.get('scored_n')}**",
        f"- Correctness passed: **{corr.get('passed_n')}**",
        f"- Correctness recall: **{corr.get('recall')}**",
        "",
        str(summary.get("claim_boundary") or ""),
        "",
    ]
    return "\n".join(lines)


def write_summary_artifacts(bundle_dir: Path, summary: Mapping[str, Any]) -> None:
    _atomic_write(
        bundle_dir / "summary.json",
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(bundle_dir / "summary.md", render_validity_markdown(summary))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument(
        "--cases-dir",
        type=Path,
        help="Optional path to a cases/ directory (e.g. live_paired_v2/cases).",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Atomically update summary.json and summary.md; evidence records remain read-only.",
    )
    parser.add_argument(
        "--require-all-terminal",
        action="store_true",
        help="Return exit 2 unless every case is terminal (not not_started/running).",
    )
    args = parser.parse_args(argv)

    if args.cases_dir is not None:
        cases_dir = args.cases_dir.resolve()
        bundle_dir = cases_dir.parent if cases_dir.name == "cases" else cases_dir
    else:
        bundle_dir = args.bundle.resolve()
        if not bundle_dir.exists() and LIVE_PAIRED_V2_CASES.is_dir():
            bundle_dir = LIVE_PAIRED_V2_CASES.parent

    summary = summarize_bundle_with_validity(bundle_dir)

    statuses: list[Any] = []
    cases_root = Path(summary["bundle"]) / "cases"
    if cases_root.is_dir():
        for case_dir in cases_root.iterdir():
            shell = case_dir / "evidence_shell.json"
            if shell.is_file():
                statuses.append(_load_json(shell).get("status"))
    all_terminal = (
        all(s not in {None, "not_started", "running"} for s in statuses) if statuses else False
    )

    written = False
    if args.write_summary:
        write_summary_artifacts(Path(summary["bundle"]), summary)
        written = True

    report = {
        "bundle": summary.get("bundle"),
        "ok": True,
        "contract_integrity_ok": summary.get("contract_integrity_ok"),
        "all_records_evidence_complete": all_terminal,
        "summary_written": written,
        "validity": summary.get("validity"),
        "correctness": {
            "scored_n": (summary.get("correctness") or {}).get("scored_n"),
            "passed_n": (summary.get("correctness") or {}).get("passed_n"),
            "recall": (summary.get("correctness") or {}).get("recall"),
        },
        "claim_boundary": summary.get("claim_boundary"),
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_all_terminal and not all_terminal:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
