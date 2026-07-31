#!/usr/bin/env python3
"""Build live_paired_v2 protocol/evidence bundles from implemented pair modules.

Default: all modules with ``IMPLEMENTED = True``.
Pre-live gate: Opentrons simulate → ``handoff_checklist.simulate_ok``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from labscriptai.runtime.live_flex_evidence_v2 import (  # noqa: E402
    MANIFEST_SCHEMA,
    PLANNED_PAIR_COUNT,
    RECORD_SCHEMA,
    render_live_summary_markdown_v2,
    summarize_live_bundle_v2,
)

from benchmarks.runtime.live_paired_v2.common import (  # noqa: E402
    COMMON_DECK,
    DEFAULT_OUTPUT,
    empty_evidence,
    oracle_for_gold,
    sha256_path,
    utc_now,
    write_json,
)
from benchmarks.runtime.live_paired_v2.pairs import (  # noqa: E402
    PAIR_MODULES,
    list_pending_pairs,
    load_implemented_pairs,
    load_pair_module,
)

VERIFY_PROTOCOL = REPO / "skills/opentrons-protocol-verify/scripts/verify_protocol.py"

PAIR_ALIASES = {
    "P1": "p1_tip_budget",
    "p1": "p1_tip_budget",
    "P2": "p2_backup_volume",
    "p2": "p2_backup_volume",
    "P3": "p3_overpressure",
    "p3": "p3_overpressure",
    "P4": "p4_contamination",
    "p4": "p4_contamination",
    "P5": "p5_pause_window",
    "p5": "p5_pause_window",
    "P6": "p6_evidence_abstain",
    "p6": "p6_evidence_abstain",
}


def _modules_for_selection(requested: Sequence[str] | None) -> list[Any]:
    if not requested or list(requested) == ["implemented"]:
        return load_implemented_pairs()
    out = []
    for raw in requested:
        name = PAIR_ALIASES.get(raw, raw)
        mod = load_pair_module(name)
        if not getattr(mod, "IMPLEMENTED", False):
            raise RuntimeError(f"pair module {name} is not IMPLEMENTED")
        out.append(mod)
    return out


def _assert_regeneration_allowed(output_dir: Path, *, force: bool) -> None:
    if not output_dir.exists():
        return
    records_dir = output_dir / "records"
    started: list[str] = []
    if records_dir.is_dir():
        for path in records_dir.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("status") != "not_started":
                started.append(path.stem)
    if started:
        raise RuntimeError(f"refusing to regenerate a bundle with started records: {sorted(started)}")
    if not force:
        raise FileExistsError(
            f"bundle already exists: {output_dir}; pass --force while all records are not_started"
        )


def probe_opentrons_simulate_available() -> dict[str, Any]:
    try:
        import opentrons.simulate  # noqa: F401

        import_ok = True
        detail = "import opentrons.simulate ok"
    except Exception as exc:  # pragma: no cover
        import_ok = False
        detail = f"import opentrons.simulate failed: {exc}"
    return {
        "ok": import_ok,
        "import_ok": import_ok,
        "verify_protocol": str(VERIFY_PROTOCOL),
        "detail": detail,
    }


def simulate_protocol(protocol_path: Path, *, timeout_s: int = 180) -> dict[str, Any]:
    if VERIFY_PROTOCOL.is_file():
        cmd = [sys.executable, str(VERIFY_PROTOCOL), "simulate", str(protocol_path)]
    else:
        cmd = [sys.executable, "-m", "opentrons.simulate", str(protocol_path)]
    completed = subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    return {
        "protocol": str(protocol_path),
        "command": cmd,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout_tail": (completed.stdout or "")[-1500:],
        "stderr_tail": (completed.stderr or "")[-1500:],
    }


def run_simulate_gate(protocols_dir: Path) -> dict[str, Any]:
    probe = probe_opentrons_simulate_available()
    protocols = sorted(protocols_dir.glob("*.py"))
    if not protocols:
        return {
            "simulate_ok": False,
            "skipped": False,
            "reason": "no protocols to simulate",
            "probe": probe,
            "results": [],
        }
    if not probe["ok"]:
        return {
            "simulate_ok": False,
            "skipped": True,
            "reason": (
                "opentrons simulate runtime not available; install via "
                "skills/opentrons-protocol-verify then re-run verify_simulate.py"
            ),
            "probe": probe,
            "results": [],
        }
    results = [simulate_protocol(path) for path in protocols]
    all_ok = all(item["ok"] for item in results)
    return {
        "simulate_ok": all_ok,
        "skipped": False,
        "reason": None if all_ok else "one or more protocols failed simulate",
        "probe": probe,
        "results": [
            {
                "protocol": Path(item["protocol"]).name,
                "ok": item["ok"],
                "returncode": item["returncode"],
                "stderr_tail": item.get("stderr_tail"),
            }
            for item in results
        ],
    }


def _materialize_case(output_dir: Path, case_id: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    protocol_relative = f"protocols/{case_id}.py"
    protocol_path = output_dir / protocol_relative
    protocol_path.write_text(str(spec["protocol_source"]), encoding="utf-8")

    design_relative = f"design-notes/{case_id}.json"
    design_path = output_dir / design_relative
    write_json(design_path, dict(spec.get("design_notes") or {}))

    setup_relative = f"physical-setup/{case_id}.json"
    write_json(output_dir / setup_relative, dict(spec["physical_setup"]))

    gold = str(spec["gold"]).upper()
    oracle = oracle_for_gold(
        gold,
        expected_policy=str(spec["expected_policy"]),
        expected_executor_action=spec.get("expected_executor_action"),
        pass_labels=list((spec.get("score_rubric") or {}).get("pass_labels") or []) or None,
    )
    rubric_relative = f"score-rubrics/{case_id}.json"
    write_json(
        output_dir / rubric_relative,
        {
            "case_id": case_id,
            "pair_id": spec["pair_id"],
            "gold": gold,
            "expected_policy": spec["expected_policy"],
            "rubric": spec.get("score_rubric") or {},
            "oracle": oracle,
        },
    )

    return {
        "case_id": case_id,
        "pair_id": spec["pair_id"],
        "variant": spec["variant"],
        "title": spec.get("title") or spec.get("source_case_title"),
        "source_case_title": spec.get("source_case_title") or spec.get("title"),
        "source_flex15_id": spec.get("source_flex15_id"),
        "protocol_file": protocol_relative,
        "protocol_sha256": sha256_path(protocol_path),
        "design_notes_file": design_relative,
        "design_notes_sha256": sha256_path(design_path),
        "physical_setup_file": setup_relative,
        "score_rubric_file": rubric_relative,
        "evidence_file": f"records/{case_id}.json",
        "physical_setup": spec["physical_setup"],
        "agent_context": spec["agent_context"],
        "expected_fault": spec["expected_fault"],
        "score_rubric": spec.get("score_rubric") or {},
        "oracle": oracle,
    }


def build_bundle(
    output_dir: Path = DEFAULT_OUTPUT,
    *,
    force: bool = False,
    pairs: Sequence[str] | None = None,
    run_simulate: bool = True,
) -> dict[str, Any]:
    modules = _modules_for_selection(pairs)
    if not modules:
        raise RuntimeError("no implemented pair modules selected")

    _assert_regeneration_allowed(output_dir, force=force)
    if output_dir.exists():
        shutil.rmtree(output_dir)

    for sub in ("protocols", "records", "design-notes", "physical-setup", "score-rubrics"):
        (output_dir / sub).mkdir(parents=True)

    pair_defs = [mod.pair_definition() for mod in modules]
    cases: list[dict[str, Any]] = []
    simulate_cmds: dict[str, str] = {}
    for mod in modules:
        for case_id, spec in mod.case_specs().items():
            case = _materialize_case(output_dir, case_id, spec)
            cases.append(case)
            write_json(
                output_dir / str(case["evidence_file"]),
                empty_evidence(case, record_schema=RECORD_SCHEMA),
            )
        if hasattr(mod, "simulate_commands"):
            simulate_cmds.update(
                mod.simulate_commands(protocol_dir=str(output_dir / "protocols"))
            )
        else:
            for case_id in mod.case_specs():
                simulate_cmds[case_id] = (
                    f".venv/bin/python -m opentrons.simulate "
                    f"{output_dir}/protocols/{case_id}.py"
                )

    if run_simulate:
        simulate_report = run_simulate_gate(output_dir / "protocols")
    else:
        simulate_report = {
            "simulate_ok": False,
            "skipped": True,
            "reason": "simulate gate skipped (--no-simulate)",
            "results": [],
        }

    pending = list_pending_pairs()
    # If caller selected a subset, pending = catalog modules not in this build.
    built_ids = {p["pair_id"] for p in pair_defs}
    if pairs and list(pairs) != ["implemented"]:
        pending = [
            load_pair_module(name).pair_definition()
            for name in PAIR_MODULES
            if getattr(load_pair_module(name), "PAIR_ID", None) not in built_ids
        ]

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "benchmark_id": "live_flex_paired_v2",
        "status": "prepared_not_executed",
        "generated_at": utc_now(),
        "n_pairs": len(pair_defs),
        "planned_pair_count": PLANNED_PAIR_COUNT,
        "pair_modules": [getattr(m, "PAIR_ID", m.__name__) for m in modules],
        "pending_pairs": pending,
        "model": "deepseek-v4-flash",
        "fallback": "none",
        "intent_to_test_denominator": len(cases),
        "transport_error_policy": "retain original run as miss; later repeats are supplemental",
        "common_deck": COMMON_DECK,
        "pairs": pair_defs,
        "cases": cases,
        "pre_live_acceptance": {
            "require_opentrons_simulate": True,
            "simulate_commands": simulate_cmds,
            "note": (
                "Protocols must pass opentrons simulate before operator handoff. "
                "Physical fault injection is live-only via physical_setup."
            ),
        },
        "handoff_checklist": {
            "simulate_ok": bool(simulate_report.get("simulate_ok")),
            "simulate_skipped": bool(simulate_report.get("skipped")),
            "simulate_reason": simulate_report.get("reason"),
            "protocols_verified": [
                item["protocol"]
                for item in simulate_report.get("results") or []
                if item.get("ok")
            ],
            "agent_context_not_native_telemetry": True,
            "control_liquid_only": True,
            "assisted_neq_autonomous": True,
            "v1_preserved": True,
            "ready_for_operator": bool(simulate_report.get("simulate_ok")),
        },
        "required_evidence": [
            "initial_state",
            "fault_evidence",
            "model_evidence",
            "gatekeeper_evidence",
            "operator_evidence",
            "execution_evidence",
            "verification_evidence",
            "media",
        ],
        "claim_boundary": (
            "No live score without complete robot and post-action evidence. "
            "Assisted ≠ Autonomous. Pre-live handoff requires handoff_checklist.simulate_ok."
        ),
        "catalog_pair_modules": list(PAIR_MODULES),
    }
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "simulate_report.json", simulate_report)

    summary = summarize_live_bundle_v2(output_dir)
    write_json(output_dir / "summary.json", summary)
    (output_dir / "summary.md").write_text(
        render_live_summary_markdown_v2(summary), encoding="utf-8"
    )

    sim_lines = [
        "# Live Flex paired v2 bundle",
        "",
        f"Pairs: {', '.join(p['pair_id'] for p in pair_defs)}",
        f"Cases: {', '.join(c['case_id'] for c in cases)}",
        f"simulate_ok: {manifest['handoff_checklist']['simulate_ok']}",
        "",
        "## Pre-live acceptance (mandatory)",
        "",
        "Each protocol must pass Opentrons simulate **before** handoff.",
        "",
        "```bash",
    ]
    for case_id in sorted(c["case_id"] for c in cases):
        sim_lines.append(
            "PYTHONPATH=.:src .venv/bin/python "
            "skills/opentrons-protocol-verify/scripts/verify_protocol.py simulate "
            f"{output_dir}/protocols/{case_id}.py"
        )
    sim_lines.extend(
        [
            "```",
            "",
            "```bash",
            "PYTHONPATH=.:src .venv/bin/python "
            "benchmarks/runtime/live_paired_v2/verify_simulate.py \\",
            f"  --bundle {output_dir} --write-report",
            "```",
            "",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(sim_lines) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=["implemented"],
        help="implemented | P1 P2 | module names",
    )
    parser.add_argument(
        "--no-simulate",
        action="store_true",
        help="Skip Opentrons simulate gate (simulate_ok stays false).",
    )
    args = parser.parse_args(argv)
    manifest = build_bundle(
        args.output,
        force=args.force,
        pairs=args.pairs,
        run_simulate=not args.no_simulate,
    )
    checklist = manifest["handoff_checklist"]
    print(
        json.dumps(
            {
                "output": str(args.output),
                "case_count": len(manifest["cases"]),
                "n_pairs": manifest["n_pairs"],
                "pairs": [p["pair_id"] for p in manifest["pairs"]],
                "simulate_ok": checklist["simulate_ok"],
                "ready_for_operator": checklist["ready_for_operator"],
            },
            indent=2,
        )
    )
    if not checklist["simulate_ok"] and not checklist.get("simulate_skipped"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
