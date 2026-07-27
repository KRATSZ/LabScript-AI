"""Flex15 shared shadow harness entry + paper-table aggregator.

Delegates case loading to ``flex15_cases`` and shadow scoring to
``recovery_shadow_benchmark.run_flex15_shadow_benchmark``. Sibling agents
write ``F0x.json`` into ``runs/runtime-flex15/shadow/``; this module merges
whatever exists into the manuscript draft table.

CLI::

    PYTHONPATH=src python -m labscriptai.runtime.flex15_shadow_benchmark
    PYTHONPATH=src python -m labscriptai.runtime.flex15_shadow_benchmark --include-negative
    PYTHONPATH=src python -m labscriptai.runtime.flex15_shadow_benchmark --aggregate-only
    PYTHONPATH=src python -m labscriptai.runtime.flex15_shadow_benchmark --provider deepseek
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .flex15_cases import load_flex15_csv
from .model_adapter import OpenAICompatibleConfig
from .shadow_feedback import is_headline_provider
from .recovery_shadow_benchmark import (
    deepseek_flex15_provider_factory,
    offline_provider_for_flex15,
    run_flex15_shadow_benchmark,
)

RESULT_SCHEMA_VERSION = "1.0"
DEFAULT_FLEX15_CSV = Path("benchmarks/runtime/flex15_runtime_recovery.csv")
DEFAULT_NEGATIVE_CSV = Path("benchmarks/runtime/flex15_negative10.csv")
DEFAULT_SHADOW_DIR = Path("runs/runtime-flex15/shadow")
DEFAULT_PAPER_ROOT = Path("runs/runtime-flex15")


def normalize_result_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Map sibling / harness JSON into the unified paper-table schema."""

    case_id = str(payload.get("case_id") or "")
    score = str(payload.get("score") or payload.get("outcome") or "")
    gold = str(payload.get("gold") or "")
    action = payload.get("proposed_action") or payload.get("candidate_action") or {}
    action_type = None
    if isinstance(action, Mapping):
        action_type = action.get("action_type")
    action_type = action_type or payload.get("action_type")

    if score in {"recover_ok", "assisted_recover", "autonomous_recover", "recover_ok_global"}:
        outcome = score if score != "recover_ok_global" else "assisted_recover"
        recover_ok = True
        safe_escalate_ok = False
        unsafe_action = False
        safe_escalate = False
    elif score == "over_escalation":
        outcome = "over_escalation"
        recover_ok = False
        safe_escalate_ok = False
        unsafe_action = False
        safe_escalate = False
    elif score in {"incomplete", "observe_incomplete"}:
        outcome = score
        recover_ok = False
        safe_escalate_ok = False
        unsafe_action = False
        safe_escalate = False
    elif score == "safe_escalate_ok":
        outcome = "safe_escalate_ok"
        recover_ok = False
        safe_escalate_ok = True
        unsafe_action = False
        safe_escalate = True
    elif score in {"unsafe", "unsafe_action"}:
        outcome = "unsafe_action"
        recover_ok = False
        safe_escalate_ok = False
        unsafe_action = True
        safe_escalate = False
    elif score == "error":
        outcome = "error"
        recover_ok = False
        safe_escalate_ok = False
        unsafe_action = False
        safe_escalate = None
    else:
        # Already-normalized rows, or fail/unknown.
        if payload.get("outcome"):
            outcome = str(payload["outcome"])
            recover_ok = bool(payload.get("recover_ok"))
            safe_escalate_ok = bool(payload.get("safe_escalate_ok"))
            unsafe_action = bool(payload.get("unsafe_action"))
            safe_escalate = payload.get("safe_escalate")
            if safe_escalate is None and safe_escalate_ok:
                safe_escalate = True
        else:
            outcome = score or "unknown"
            recover_ok = False
            safe_escalate_ok = False
            unsafe_action = False
            safe_escalate = None

    platform = str(payload.get("platform") or "Opentrons Flex")
    fault = str(payload.get("fault") or payload.get("anomaly") or payload.get("title") or "")
    notes = str(
        payload.get("notes")
        or payload.get("evidence_notes")
        or ""
    )
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "platform": platform,
        "case_id": case_id,
        "group": payload.get("group", ""),
        "fault": fault,
        "error_signal": payload.get("error_signal", ""),
        "gold": gold,
        "outcome": outcome,
        "recover_ok": recover_ok,
        "safe_escalate_ok": safe_escalate_ok,
        "safe_escalate": safe_escalate,
        "unsafe_action": unsafe_action,
        "action_type": action_type,
        "gatekeeper_status": payload.get("gatekeeper_status"),
        "model_id": payload.get("model_id", ""),
        "provider": payload.get("provider", ""),
        "notes": notes,
        "generated_at": payload.get("generated_at") or _utc_now(),
        "source_score": score,
    }


def load_result_jsons(shadow_dir: Path) -> list[dict[str, Any]]:
    """Load sibling-written + harness-written per-case JSON results."""

    if not shadow_dir.exists():
        return []
    results: list[dict[str, Any]] = []
    skip = {
        "summary.json",
        "summary_partial.json",
        "aggregate_manifest.json",
        "flex15_results_table.csv",
    }
    for path in sorted(shadow_dir.glob("*.json")):
        if path.name in skip or path.name.endswith("_summary.json"):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, Mapping) or "case_id" not in payload:
            continue
        results.append(normalize_result_row(payload))
    return results


def aggregate_flex15_results(
    *,
    shadow_dir: Path,
    paper_root: Path,
    extra_rows: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Merge whatever F0x/N0x/Hamilton JSON exists into CSV + paper markdown."""

    shadow_dir.mkdir(parents=True, exist_ok=True)
    paper_root.mkdir(parents=True, exist_ok=True)

    rows = load_result_jsons(shadow_dir)
    if extra_rows:
        rows.extend(normalize_result_row(item) for item in extra_rows)

    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "")
        if not case_id:
            continue
        prev = by_id.get(case_id)
        if prev is None or str(row.get("generated_at", "")) >= str(prev.get("generated_at", "")):
            by_id[case_id] = row

    ordered = sorted(by_id.values(), key=_case_sort_key)
    headline_rows = [r for r in ordered if is_headline_provider(str(r.get("provider") or ""))]
    table_csv = shadow_dir / "flex15_results_table.csv"
    paper_md = paper_root / "PAPER_TABLE_DRAFT.md"

    fieldnames = [
        "platform",
        "case_id",
        "fault",
        "gold",
        "outcome",
        "safe_escalate",
        "recover_ok",
        "unsafe_action",
        "action_type",
        "gatekeeper_status",
        "model_id",
        "provider",
        "notes",
    ]
    with table_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in ordered:
            writer.writerow(
                {
                    "platform": row.get("platform", ""),
                    "case_id": row.get("case_id", ""),
                    "fault": row.get("fault", ""),
                    "gold": row.get("gold", ""),
                    "outcome": row.get("outcome", ""),
                    "safe_escalate": _fmt_bool(row.get("safe_escalate")),
                    "recover_ok": _fmt_bool(row.get("recover_ok")),
                    "unsafe_action": _fmt_bool(row.get("unsafe_action")),
                    "action_type": row.get("action_type", ""),
                    "gatekeeper_status": row.get("gatekeeper_status", ""),
                    "model_id": row.get("model_id", ""),
                    "provider": row.get("provider", ""),
                    "notes": row.get("notes", ""),
                }
            )

    paper_md.write_text(_paper_table_markdown(headline_rows or ordered), encoding="utf-8")
    aggregate = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "row_count": len(ordered),
        "headline_row_count": len(headline_rows),
        "table_csv": str(table_csv),
        "paper_md": str(paper_md),
        "case_ids": [row.get("case_id") for row in ordered],
        "recover_ok": sum(1 for r in headline_rows if r.get("recover_ok")),
        "safe_escalate_ok": sum(1 for r in headline_rows if r.get("safe_escalate_ok")),
        "unsafe_action": sum(1 for r in headline_rows if r.get("unsafe_action")),
        "headline_provider_only": True,
    }
    (shadow_dir / "aggregate_manifest.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return aggregate


def annotate_platform_on_results(shadow_dir: Path, cases_by_id: Mapping[str, Any]) -> None:
    """Stamp platform onto freshly written case JSON when the CSV provides it."""

    for case_id, case in cases_by_id.items():
        path = shadow_dir / f"{case_id}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        platform = getattr(case, "platform", None) or "Opentrons Flex"
        if payload.get("platform") != platform:
            payload["platform"] = platform
            if not payload.get("generated_at"):
                payload["generated_at"] = _utc_now()
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
                encoding="utf-8",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_FLEX15_CSV)
    parser.add_argument("--negative-cases", type=Path, default=None)
    parser.add_argument(
        "--include-negative",
        action="store_true",
        help=f"Also run {DEFAULT_NEGATIVE_CSV}",
    )
    parser.add_argument("--case-id", action="append", default=[], help="Restrict to case_id(s)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_SHADOW_DIR)
    parser.add_argument("--paper-root", type=Path, default=DEFAULT_PAPER_ROOT)
    parser.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Skip running cases; only merge existing shadow JSON into paper table",
    )
    args = parser.parse_args(argv)

    if args.aggregate_only:
        aggregate = aggregate_flex15_results(shadow_dir=args.output_dir, paper_root=args.paper_root)
        print(json.dumps(aggregate, indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    case_ids = tuple(cid.strip() for cid in args.case_id if cid.strip()) or None
    # When negatives are included with an explicit case filter, load both tables then filter.
    flex_ids = None
    neg_ids = None
    if case_ids is not None:
        flex_ids = tuple(cid for cid in case_ids if cid.upper().startswith("F"))
        neg_ids = tuple(cid for cid in case_ids if cid.upper().startswith("N"))

    if args.provider == "deepseek":
        config = OpenAICompatibleConfig.from_env(
            default_base_url="https://api.deepseek.com",
            default_model="deepseek-v4-flash",
        )
        factory = deepseek_flex15_provider_factory(config)
        model_id = config.model
        provider = "deepseek"
    else:
        factory = offline_provider_for_flex15
        model_id = "offline-flex15"
        provider = "offline"

    summaries: list[dict[str, Any]] = []

    run_flex = True
    if case_ids is not None and not flex_ids and (args.include_negative or args.negative_cases):
        run_flex = False
    if run_flex and (case_ids is None or flex_ids):
        summary = run_flex15_shadow_benchmark(
            csv_path=args.cases,
            output_dir=args.output_dir,
            candidate_provider_factory=factory,
            model_id=model_id,
            case_ids=flex_ids if case_ids is not None else None,
        )
        summaries.append(summary)
        loaded = load_flex15_csv(args.cases, case_ids=flex_ids if case_ids is not None else None)
        annotate_platform_on_results(args.output_dir, {c.case_id: c for c in loaded})
        _stamp_provider(args.output_dir, [c.case_id for c in loaded], provider)

    negative_path = args.negative_cases
    if args.include_negative and negative_path is None:
        negative_path = DEFAULT_NEGATIVE_CSV
    if negative_path is not None:
        neg_case_ids = neg_ids if case_ids is not None else None
        if neg_case_ids is None or len(neg_case_ids) > 0:
            summary = run_flex15_shadow_benchmark(
                csv_path=negative_path,
                output_dir=args.output_dir,
                candidate_provider_factory=factory,
                model_id=model_id,
                case_ids=neg_case_ids,
            )
            summaries.append(summary)
            loaded = load_flex15_csv(negative_path, case_ids=neg_case_ids)
            annotate_platform_on_results(args.output_dir, {c.case_id: c for c in loaded})
            _stamp_provider(args.output_dir, [c.case_id for c in loaded], provider)

    aggregate = aggregate_flex15_results(shadow_dir=args.output_dir, paper_root=args.paper_root)
    combined = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "provider": provider,
        "model_id": model_id,
        "run_summaries": [
            {
                "case_count": s.get("case_count"),
                "recover_ok_count": s.get("recover_ok_count"),
                "safe_escalate_ok_count": s.get("safe_escalate_ok_count"),
                "unsafe_count": s.get("unsafe_count"),
                "fail_count": s.get("fail_count"),
                "error_count": s.get("error_count"),
            }
            for s in summaries
        ],
        "aggregate": aggregate,
    }
    print(json.dumps(combined, indent=2, ensure_ascii=False, sort_keys=True))
    error_count = sum(int(s.get("error_count") or 0) for s in summaries)
    return 0 if error_count == 0 else 1


def _stamp_provider(shadow_dir: Path, case_ids: list[str], provider: str) -> None:
    for case_id in case_ids:
        path = shadow_dir / f"{case_id}.json"
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        payload["provider"] = provider
        if not payload.get("generated_at"):
            payload["generated_at"] = _utc_now()
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )


def _case_sort_key(row: Mapping[str, Any]) -> tuple[int, str]:
    case_id = str(row.get("case_id", ""))
    match = re.match(r"^([A-Za-z]+)(\d+)$", case_id)
    if match:
        prefix, num = match.group(1).upper(), int(match.group(2))
        order = {"F": 0, "N": 1, "H": 2, "HN": 3}.get(prefix, 9)
        return (order, f"{num:04d}")
    return (8, case_id)


def _fmt_bool(value: Any) -> str:
    if value is None:
        return ""
    return "true" if bool(value) else "false"


def _paper_table_markdown(rows: list[Mapping[str, Any]]) -> str:
    lines = [
        "# Runtime recovery — preliminary paper table",
        "",
        "_Draft merged from `runs/runtime-flex15/shadow/*.json`. "
        "Flex = shadow proposal + Gatekeeper; Hamilton = separate error-replay; "
        "Tecan = deferred (no live fault telemetry)._",
        "",
        "| Platform | Case | Fault | Gold | Outcome | Safe escalate? | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not rows:
        lines.append(
            "| _(none yet)_ |  |  |  |  |  | Run harness or drop F0x.json into shadow/ |"
        )
    for row in rows:
        safe = row.get("safe_escalate")
        if safe is None:
            safe_cell = ""
        else:
            safe_cell = "yes" if safe else "no"
        notes = str(row.get("notes") or "").replace("|", "/")
        if len(notes) > 120:
            notes = notes[:117] + "..."
        lines.append(
            "| {platform} | {case_id} | {fault} | {gold} | {outcome} | {safe} | {notes} |".format(
                platform=row.get("platform", ""),
                case_id=row.get("case_id", ""),
                fault=str(row.get("fault", "")).replace("|", "/"),
                gold=row.get("gold", ""),
                outcome=row.get("outcome", ""),
                safe=safe_cell,
                notes=notes,
            )
        )
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- rows: {len(rows)}",
            f"- recover_ok (headline providers): {sum(1 for r in rows if r.get('recover_ok'))}",
            f"- safe_escalate_ok (headline providers): {sum(1 for r in rows if r.get('safe_escalate_ok'))}",
            f"- unsafe_action (headline providers): {sum(1 for r in rows if r.get('unsafe_action'))}",
            "",
        ]
    )
    return "\n".join(lines)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
