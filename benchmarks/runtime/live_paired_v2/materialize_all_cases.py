#!/usr/bin/env python3
"""Materialize all 12 live_paired_v2 cases into the repo cases/ tree.

Writes ``benchmarks/runtime/live_paired_v2/cases/<CASE_ID>/`` from pair
``case_specs()`` so the bundle is self-contained for handoff (not only under
``runs/runtime-flex15/live_paired_v2/``).

Layout matches existing LP203/LP205 repo cases:
  protocol.py, agent_context.json, physical_setup.json, score_rubric.json,
  evidence_shell.json, README.md, design_notes.json

Does not delete alias dirs (``P3_E`` / ``P5_*``). No simulate / DeepSeek.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from benchmarks.runtime.live_paired_v2.common import (  # noqa: E402
    oracle_for_gold,
    write_json,
)
from benchmarks.runtime.live_paired_v2.pairs import load_implemented_pairs  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parent
CANONICAL_IDS = (
    "LP201R",
    "LP201E",
    "LP202R",
    "LP202E",
    "LP203R",
    "LP203E",
    "LP204R",
    "LP204E",
    "LP205R",
    "LP205E",
    "LP206R",
    "LP206U",
)


def _score_rubric(case_id: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    rubric = dict(spec.get("score_rubric") or {})
    if "oracle" in spec:
        oracle = dict(spec["oracle"])
    else:
        oracle = oracle_for_gold(
            str(spec["gold"]),
            expected_policy=str(spec["expected_policy"]),
            expected_executor_action=spec.get("expected_executor_action"),
            pass_labels=list(rubric.get("pass_labels") or []) or None,
        )
    # Match existing repo case score_rubric.json shape (LP203R).
    return {
        "case_id": case_id,
        "expected_policy": oracle.get("expected_policy") or spec.get("expected_policy"),
        "gold": oracle.get("gold") or spec.get("gold"),
        "rubric": {
            "fail_unsafe": list(rubric.get("fail_unsafe") or []),
            "incomplete_if": rubric.get("incomplete_if"),
            "pass": list(rubric.get("pass") or []),
            "pass_labels": list(
                oracle.get("pass_labels") or rubric.get("pass_labels") or []
            ),
        },
    }


def materialize_case(cases_root: Path, case_id: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    case_dir = cases_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    (case_dir / "protocol.py").write_text(str(spec["protocol_source"]), encoding="utf-8")
    write_json(case_dir / "agent_context.json", dict(spec["agent_context"]))
    write_json(case_dir / "physical_setup.json", dict(spec["physical_setup"]))
    write_json(case_dir / "score_rubric.json", _score_rubric(case_id, spec))
    write_json(
        case_dir / "evidence_shell.json",
        {
            "case_id": case_id,
            "pair_id": spec["pair_id"],
            "status": "not_started",
        },
    )
    if spec.get("design_notes"):
        write_json(case_dir / "design_notes.json", dict(spec["design_notes"]))

    rel = f"benchmarks/runtime/live_paired_v2/cases/{case_id}/protocol.py"
    (case_dir / "README.md").write_text(
        f"# {case_id}\n\n"
        f"```bash\n"
        f".venv/bin/python skills/opentrons-protocol-verify/scripts/verify_protocol.py "
        f"simulate {rel}\n"
        f"```\n",
        encoding="utf-8",
    )

    return {
        "case_id": case_id,
        "pair_id": spec["pair_id"],
        "variant": spec.get("variant"),
        "gold": spec.get("gold"),
        "case_dir": str(case_dir.relative_to(REPO)),
    }


def collect_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for mod in load_implemented_pairs():
        specs.update(mod.case_specs())
    missing = [cid for cid in CANONICAL_IDS if cid not in specs]
    if missing:
        raise RuntimeError(f"missing case specs: {missing}")
    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Parent of cases/ (default: benchmarks/runtime/live_paired_v2)",
    )
    args = parser.parse_args(argv)

    cases_root = args.output_root / "cases"
    cases_root.mkdir(parents=True, exist_ok=True)
    specs = collect_specs()
    written = [materialize_case(cases_root, cid, specs[cid]) for cid in CANONICAL_IDS]
    print(
        json.dumps(
            {
                "output": str(cases_root),
                "case_count": len(written),
                "cases": [row["case_id"] for row in written],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
