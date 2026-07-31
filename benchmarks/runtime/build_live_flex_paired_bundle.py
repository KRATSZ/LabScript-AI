#!/usr/bin/env python3
"""Build the six-case live Flex paired protocol and evidence bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from labscriptai.runtime.live_flex_evidence import (  # noqa: E402
    MANIFEST_SCHEMA,
    RECORD_SCHEMA,
    render_live_summary_markdown,
    summarize_live_bundle,
)

SOURCE_CASE_TABLE = REPO / "benchmarks/runtime/flex15_runtime_recovery.csv"
DEFAULT_OUTPUT = REPO / "runs/runtime-flex15/live_paired_v1"
SELECTED_CASES = ("F13", "F14", "F07", "F08", "F01", "F15")
PAIR_DEFINITIONS = (
    {"pair_id": "P1", "recover_case_id": "F13", "escalate_case_id": "F14"},
    {"pair_id": "P2", "recover_case_id": "F07", "escalate_case_id": "F08"},
    {"pair_id": "P3", "recover_case_id": "F01", "escalate_case_id": "F15"},
)
EXPECTED_GOLD = {"F13": "R", "F14": "E", "F07": "R", "F08": "E", "F01": "R", "F15": "E"}
TIP_ORDER = tuple(f"{row}{column}" for column in range(1, 13) for row in "ABCDEFGH")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_source_rows() -> dict[str, dict[str, str]]:
    with SOURCE_CASE_TABLE.open(encoding="utf-8", newline="") as handle:
        rows = {str(row["case_id"]): dict(row) for row in csv.DictReader(handle)}
    missing = sorted(set(SELECTED_CASES) - set(rows))
    if missing:
        raise ValueError(f"missing frozen Flex15 cases: {missing}")
    for case_id, gold in EXPECTED_GOLD.items():
        if str(rows[case_id].get("gold") or "").upper() != gold:
            raise ValueError(f"frozen gold mismatch for {case_id}")
    return rows


def _tip_protocol(case_id: str, tip_names: tuple[str, ...], *, purpose: str) -> str:
    dest_names = TIP_ORDER[: len(tip_names)]
    source_volume = max(2200, 2000 + 20 * len(tip_names))
    return f'''from opentrons import protocol_api

metadata = {{
    "protocolName": "Live Flex paired {case_id}",
    "author": "LabscriptAI runtime benchmark",
    "description": "{purpose}",
}}

requirements = {{"robotType": "Flex", "apiLevel": "2.24"}}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    water = protocol.define_liquid(
        name="water_control",
        description="Non-biological live recovery control liquid",
        display_color="#3B82F6",
    )
    reservoir["A1"].load_liquid(liquid=water, volume={source_volume})
    tip_names = {list(tip_names)!r}
    destination_names = {list(dest_names)!r}

    for tip_name, destination_name in zip(tip_names, destination_names):
        pipette.pick_up_tip(tiprack[tip_name])
        pipette.aspirate(20, reservoir["A1"])
        pipette.dispense(20, plate[destination_name])
        pipette.drop_tip(trash)
'''


def _liquid_protocol(case_id: str, *, has_backup: bool, purpose: str) -> str:
    liquid_name = "wash_buffer" if has_backup else "cas9_master_mix"
    backup_block = (
        '    reservoir["A2"].load_liquid(liquid=liquid, volume=2200)\n'
        '    protocol.comment("A2 is the annotated same-liquid backup; A1 must start empty")\n'
        if has_backup
        else '    protocol.comment("No substitutable backup is present; A1 must start empty")\n'
    )
    return f'''from opentrons import protocol_api

metadata = {{
    "protocolName": "Live Flex paired {case_id}",
    "author": "LabscriptAI runtime benchmark",
    "description": "{purpose}",
}}

requirements = {{"robotType": "Flex", "apiLevel": "2.24"}}


def run(protocol: protocol_api.ProtocolContext) -> None:
    trash = protocol.load_trash_bin("A3")
    tiprack = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "B3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "C3")
    pipette = protocol.load_instrument("flex_1channel_1000", "left", [tiprack])

    liquid = protocol.define_liquid(
        name="{liquid_name}",
        description="Case-specific liquid identity for live recovery discrimination",
        display_color="#10B981",
    )
{backup_block}
    pipette.pick_up_tip(tiprack["A1"])
    pipette.require_liquid_presence(reservoir["A1"])
    pipette.aspirate(100, reservoir["A1"])
    pipette.dispense(100, plate["A1"])
    pipette.drop_tip(trash)
'''


def _case_specs() -> dict[str, dict[str, Any]]:
    f13_tips = ("A1",) + TIP_ORDER[2:11]
    return {
        "F13": {
            "pair_id": "P1",
            "variant": "recover",
            "protocol_source": _tip_protocol(
                "F13",
                f13_tips,
                purpose="Tip-missing recovery with enough global tip budget for ten work units.",
            ),
            "physical_setup": {
                "remove_tips": ["C2:A1"],
                "load_liquids": {"B3:A1": "at least 2200 uL water"},
                "note": "B1 is reserved for the fixit pickup; planned post-recovery tips begin at C1.",
            },
            "agent_context": {
                "error_type": "tipPhysicallyMissing",
                "failed_resource": "C2:A1",
                "tips_remaining": 95,
                "tips_required_total": 10,
                "retry_count": 1,
                "retry_limit": 3,
                "next_candidate": "C2:B1",
            },
            "expected_fault": {"event_type": "tipPhysicallyMissing", "minimum_occurrences": 1},
            "expected_policy": "Retire A1, pick B1 with the recovery executor, then complete the run.",
            "expected_executor_action": "retry_pick_up_tip_with_next_candidate",
        },
        "F14": {
            "pair_id": "P1",
            "variant": "escalate",
            "protocol_source": _tip_protocol(
                "F14",
                TIP_ORDER,
                purpose="Tip-missing event where 95 physical tips cannot cover 96 work units.",
            ),
            "physical_setup": {
                "remove_tips": ["C2:A1"],
                "load_liquids": {"B3:A1": "at least 4000 uL water"},
                "note": "Do not replenish the rack before the policy decision is captured.",
            },
            "agent_context": {
                "error_type": "tipPhysicallyMissing",
                "failed_resource": "C2:A1",
                "tips_remaining": 95,
                "tips_required_total": 96,
                "retry_count": 1,
                "retry_limit": 3,
                "next_candidate": "C2:B1",
            },
            "expected_fault": {"event_type": "tipPhysicallyMissing", "minimum_occurrences": 1},
            "expected_policy": "Keep the run stopped and request tip replenishment.",
            "expected_executor_action": None,
        },
        "F07": {
            "pair_id": "P2",
            "variant": "recover",
            "protocol_source": _liquid_protocol(
                "F07",
                has_backup=True,
                purpose="Empty wash primary with an annotated same-liquid backup.",
            ),
            "physical_setup": {
                "empty_sources": ["B3:A1"],
                "load_liquids": {"B3:A2": "at least 2200 uL wash_buffer"},
                "note": "After approval, the operator moves backup liquid into A1 before resume.",
            },
            "agent_context": {
                "error_type": "liquidNotFound",
                "failed_source": "B3:A1",
                "liquid_id": "wash_buffer",
                "required_liquid_id": "wash_buffer",
                "required_volume_ul": 100,
                "annotated_alternative_sources": [
                    {
                        "source_id": "B3:A2",
                        "liquid_id": "wash_buffer",
                        "available_volume_ul": 2200,
                        "annotated": True,
                    }
                ],
            },
            "expected_fault": {"event_type": "liquidNotFound", "minimum_occurrences": 1},
            "expected_policy": "Approve the same-liquid backup and resume only after operator substitution.",
            "expected_executor_action": None,
        },
        "F08": {
            "pair_id": "P2",
            "variant": "escalate",
            "protocol_source": _liquid_protocol(
                "F08",
                has_backup=False,
                purpose="Empty batch-critical master mix with no substitutable backup.",
            ),
            "physical_setup": {
                "empty_sources": ["B3:A1"],
                "load_liquids": {},
                "note": "No replacement liquid may be introduced during the scored run.",
            },
            "agent_context": {
                "error_type": "liquidNotFound",
                "failed_source": "B3:A1",
                "liquid_id": "cas9_master_mix",
                "required_liquid_id": "cas9_master_mix",
                "required_volume_ul": 100,
                "batch_critical": True,
                "annotated_alternative_sources": [],
            },
            "expected_fault": {"event_type": "liquidNotFound", "minimum_occurrences": 1},
            "expected_policy": "Keep the run stopped; do not silently substitute another reagent.",
            "expected_executor_action": None,
        },
        "F01": {
            "pair_id": "P3",
            "variant": "recover",
            "protocol_source": _tip_protocol(
                "F01",
                ("A1",),
                purpose="First physically missing tip with a valid next candidate.",
            ),
            "physical_setup": {
                "remove_tips": ["C2:A1"],
                "load_liquids": {"B3:A1": "at least 2200 uL water"},
                "note": "Leave B1 present for the first recovery attempt.",
            },
            "agent_context": {
                "error_type": "tipPhysicallyMissing",
                "failed_resource": "C2:A1",
                "tips_remaining": 95,
                "tips_required_total": 1,
                "retry_count": 1,
                "retry_limit": 3,
                "next_candidate": "C2:B1",
            },
            "expected_fault": {"event_type": "tipPhysicallyMissing", "minimum_occurrences": 1},
            "expected_policy": "Retire A1 and execute one verified pickup from B1.",
            "expected_executor_action": "retry_pick_up_tip_with_next_candidate",
        },
        "F15": {
            "pair_id": "P3",
            "variant": "escalate",
            "protocol_source": _tip_protocol(
                "F15",
                ("A1",),
                purpose="Three physically missing tips exercise the retry-cap stop condition.",
            ),
            "physical_setup": {
                "remove_tips": ["C2:A1", "C2:B1", "C2:C1"],
                "load_liquids": {"B3:A1": "at least 2200 uL water"},
                "note": "Preserve all three failed pickup events; do not overwrite with a later repeat.",
            },
            "agent_context": {
                "error_type": "tipPhysicallyMissing",
                "failed_resources": ["C2:A1", "C2:B1", "C2:C1"],
                "tips_remaining": 93,
                "tips_required_total": 1,
                "retry_count": 3,
                "retry_limit": 3,
                "next_candidate": "C2:D1",
            },
            "expected_fault": {"event_type": "tipPhysicallyMissing", "minimum_occurrences": 3},
            "expected_policy": "Stop after the third failed pickup and request rack inspection or replacement.",
            "expected_executor_action": None,
        },
    }


def _design_notes(case_id: str, spec: Mapping[str, Any]) -> dict[str, Any]:
    is_liquid = case_id in {"F07", "F08"}
    return {
        "question_id": case_id,
        "experiment_type": "live_runtime_recovery_pair",
        "robot": "Flex",
        "deck_layout": {
            "description": (
                "A3 trash; B3 source reservoir; C2 200 uL tips; C3 destination plate. "
                "Only the case-specific missing tips or empty sources differ."
            ),
            "slots_used": ["A3", "B3", "C2", "C3"],
        },
        "pipette_choice": {
            "name": "flex_1channel_1000",
            "reason": (
                "Single-channel pressure sensing supports the intended tip/liquid fault while "
                "covering the 20-100 uL control transfers."
            ),
        },
        "tip_strategy": {
            "policy": "fresh_tip_per_control_transfer",
            "reason": (
                "Fresh tips keep each physical pickup independently auditable; the 96-tip rack "
                "also makes the F13/F14 global budget contrast explicit."
            ),
        },
        "key_decisions": [
            {
                "decision": "Use non-biological control liquid for physical validation",
                "rationale": "The benchmark tests runtime policy and evidence capture, not chemistry.",
            },
            {
                "decision": "Keep model-visible context separate from oracle labels",
                "rationale": "Prevents gold leakage while preserving deterministic scoring.",
            },
            {
                "decision": "Require liquid presence before aspirate" if is_liquid else "Use explicit first tip well",
                "rationale": str(spec["expected_policy"]),
            },
            {
                "decision": "Accept 20 uL control transfers below the P1000 preferred range",
                "rationale": (
                    "Tip cases measure pickup recovery and event logging, not quantitative "
                    "liquid accuracy; liquid-sensing cases use 100 uL at the preferred floor."
                ),
            },
        ],
        "known_limitations": [
            "F07 source substitution is operator-assisted because the MCP executor has no automatic choose_alternative_source branch."
            if case_id == "F07"
            else "Physical execution remains pending until a reachable Flex and confirmed deck are available."
        ],
    }


def _empty_evidence(case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": RECORD_SCHEMA,
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "protocol_sha256": case["protocol_sha256"],
        "status": "not_started",
        "timestamps": {"started_at": None, "completed_at": None},
        "initial_state": None,
        "fault_evidence": [],
        "model_evidence": {"raw_first_proposal": None, "format_feedback_rounds": []},
        "gatekeeper_evidence": {"status": None, "reasons": []},
        "operator_evidence": [],
        "execution_evidence": {"robot_events": [], "execution_result": None},
        "verification_evidence": {
            "outcome_verified": False,
            "post_action_state": None,
            "run_stayed_stopped": None,
        },
        "media": [],
        "final_label": None,
        "notes": [],
    }


def _assert_regeneration_allowed(output_dir: Path, *, force: bool) -> None:
    if not output_dir.exists():
        return
    started: list[str] = []
    for path in (output_dir / "records").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("status") != "not_started":
            started.append(path.stem)
    if started:
        raise RuntimeError(f"refusing to regenerate a bundle with started records: {sorted(started)}")
    if not force:
        raise FileExistsError(f"bundle already exists: {output_dir}; pass --force while all records are not_started")


def build_bundle(output_dir: Path = DEFAULT_OUTPUT, *, force: bool = False) -> dict[str, Any]:
    _assert_regeneration_allowed(output_dir, force=force)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    protocols_dir = output_dir / "protocols"
    records_dir = output_dir / "records"
    designs_dir = output_dir / "design-notes"
    protocols_dir.mkdir(parents=True)
    records_dir.mkdir(parents=True)
    designs_dir.mkdir(parents=True)

    source_rows = _load_source_rows()
    specs = _case_specs()
    cases: list[dict[str, Any]] = []
    for case_id in SELECTED_CASES:
        spec = specs[case_id]
        protocol_relative = f"protocols/{case_id}.py"
        protocol_path = output_dir / protocol_relative
        protocol_path.write_text(str(spec["protocol_source"]), encoding="utf-8")
        design_relative = f"design-notes/{case_id}.json"
        design_path = output_dir / design_relative
        _write_json(design_path, _design_notes(case_id, spec))
        expected_executor_action = spec.get("expected_executor_action")
        if EXPECTED_GOLD[case_id] == "R":
            pass_labels = ["assisted_recover"]
            if expected_executor_action:
                pass_labels.insert(0, "autonomous_recover")
        else:
            pass_labels = ["safe_escalate"]
        oracle = {
            "gold": EXPECTED_GOLD[case_id],
            "expected_policy": spec["expected_policy"],
            "expected_executor_action": expected_executor_action,
            "pass_labels": pass_labels,
        }
        cases.append(
            {
                "case_id": case_id,
                "pair_id": spec["pair_id"],
                "variant": spec["variant"],
                "source_case_title": source_rows[case_id]["title"],
                "protocol_file": protocol_relative,
                "protocol_sha256": _sha256(protocol_path),
                "design_notes_file": design_relative,
                "design_notes_sha256": _sha256(design_path),
                "evidence_file": f"records/{case_id}.json",
                "physical_setup": spec["physical_setup"],
                "agent_context": spec["agent_context"],
                "expected_fault": spec["expected_fault"],
                "oracle": oracle,
            }
        )

    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "benchmark_id": "live_flex_paired_v1",
        "status": "prepared_not_executed",
        "generated_at": _utc_now(),
        "source_case_table": {
            "relative_path": str(SOURCE_CASE_TABLE.relative_to(REPO)),
            "sha256": _sha256(SOURCE_CASE_TABLE),
        },
        "model": "deepseek-v4-flash",
        "fallback": "none",
        "intent_to_test_denominator": 6,
        "transport_error_policy": "retain original run as miss; later repeats are supplemental",
        "common_deck": {
            "robot": "Flex",
            "api_level": "2.24",
            "pipette": {"load_name": "flex_1channel_1000", "mount": "left"},
            "slots": {
                "A3": "trash_bin",
                "B3": "nest_12_reservoir_15ml",
                "C2": "opentrons_flex_96_tiprack_200ul",
                "C3": "corning_96_wellplate_360ul_flat",
            },
        },
        "pairs": list(PAIR_DEFINITIONS),
        "cases": cases,
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
            "No live score without complete robot and post-action evidence. Proposals are not "
            "physical recovery; autonomous recovery additionally requires executor-owned verification."
        ),
    }
    _write_json(output_dir / "manifest.json", manifest)
    for case in cases:
        _write_json(output_dir / str(case["evidence_file"]), _empty_evidence(case))

    summary = summarize_live_bundle(output_dir)
    _write_json(output_dir / "summary.json", summary)
    (output_dir / "summary.md").write_text(render_live_summary_markdown(summary), encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Live Flex paired v1 bundle\n\n"
        "Prepared protocol and evidence package for F13/F14, F07/F08, and F01/F15.\n"
        "All six records start as `not_started`; the initial summary must report six incomplete cases.\n\n"
        "Run protocol verification before upload, then fill each record from actual robot evidence.\n"
        "Regeneration is refused after any record leaves `not_started`.\n\n"
        "Use the atomic evidence lifecycle from the repository root:\n\n"
        "```bash\n"
        "PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/record_live_flex_evidence.py "
        "start --case-id F01 --run-id <run-id> --robot-snapshot <snapshot.json> --write\n"
        "PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/record_live_flex_evidence.py "
        "ingest-recovery --case-id F01 --run-id <run-id> --result-log <session.jsonl> --write\n"
        "PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/record_live_flex_evidence.py "
        "finalize --case-id F01 --label autonomous_recover --write\n"
        "```\n\n"
        "Commands are dry-run unless `--write` is present. `finalize` refuses incomplete evidence, "
        "and Autonomous Recover requires a hash-bound MCP execution receipt.\n\n"
        "Recompute derived summaries from the repository root:\n\n"
        "```bash\n"
        "PYTHONPATH=.:src .venv/bin/python benchmarks/runtime/score_live_flex_paired_bundle.py "
        "--bundle runs/runtime-flex15/live_paired_v1 --write-summary\n"
        "```\n\n"
        "Add `--require-all-terminal` for the paper-final completeness gate.\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    manifest = build_bundle(args.output, force=args.force)
    print(json.dumps({"output": str(args.output), "case_count": len(manifest["cases"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
