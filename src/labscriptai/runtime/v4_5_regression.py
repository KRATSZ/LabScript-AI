"""Run the deterministic v4.5 development policy regression panel."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .actions import CandidateAction
from .policy_v4_5 import POLICY_VERSION, action_matches_v4_5
from .shadow_feedback_v4_5 import run_gatekeeper_feedback_loop_v4_5
from .state import RuntimeState

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST = REPO_ROOT / "benchmarks/runtime/runtime_v4_5_regression.json"
DEFAULT_OUTPUT = REPO_ROOT / "runs/runtime-v4_5-regression"
SCHEMA_VERSION = "runtime_v4_5_regression.v1"


def run_regression(
    manifest_path: Path = DEFAULT_MANIFEST,
    output_dir: Path | None = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"manifest schema must be {SCHEMA_VERSION}")

    records = [_run_case(raw) for raw in manifest.get("cases") or ()]
    if not records:
        raise ValueError("v4.5 regression manifest has no cases")
    case_ids = [record["case_id"] for record in records]
    if any(not case_id for case_id in case_ids) or len(case_ids) != len(set(case_ids)):
        raise ValueError("case_id values must be non-empty and unique")

    passed = sum(bool(record["passed"]) for record in records)
    summary = {
        "schema_version": "runtime_v4_5_regression_summary.v1",
        "policy_version": POLICY_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "case_count": len(records),
        "passed": passed,
        "failed": len(records) - passed,
        "all_passed": passed == len(records),
        "claim_boundary": (
            "Deterministic development regression only; not a model capability, "
            "confirmatory holdout, or live robot result."
        ),
        "records": records,
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")
    return summary


def _run_case(raw: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(raw.get("case_id") or "")
    kind = str(raw.get("kind") or "")
    state = RuntimeState.from_mapping(raw.get("state") or {})
    action = CandidateAction.from_mapping(raw.get("action") or {})

    if kind == "gatekeeper":
        expected = str(raw.get("expected_status") or "")
        loop = run_gatekeeper_feedback_loop_v4_5(
            state=state,
            propose=lambda _state, _feedback: action,
            allowed_action_types=(action.action_type,),
        )
        decision = loop.final_decision
        if decision is None:
            raise ValueError(f"{case_id}: feedback loop produced no decision")
        actual: Any = decision.status
        details = {"feedback_loop": loop.to_dict()}
    elif kind == "matcher":
        expected = bool(raw.get("expected_match"))
        spec = raw.get("spec") or {}
        if not isinstance(spec, Mapping):
            raise ValueError(f"{case_id}: matcher spec must be an object")
        actual = action_matches_v4_5(action, spec, state)
        details = {"matched": actual}
    else:
        raise ValueError(f"{case_id}: unsupported regression kind {kind!r}")

    return {
        "case_id": case_id,
        "kind": kind,
        "expected": expected,
        "actual": actual,
        "passed": actual == expected,
        "details": details,
    }


def _summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Runtime v4.5 development regression",
        "",
        f"Policy: `{summary['policy_version']}`.",
        "",
        "| Case | Kind | Expected | Actual | Pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in summary["records"]:
        lines.append(
            f"| {record['case_id']} | {record['kind']} | {record['expected']} | "
            f"{record['actual']} | {'yes' if record['passed'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            f"Result: **{summary['passed']}/{summary['case_count']} passed**.",
            "",
            str(summary["claim_boundary"]),
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = run_regression(args.manifest, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
