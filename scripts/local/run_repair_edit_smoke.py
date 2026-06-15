#!/usr/bin/env python3
"""Run forced simulation-repair smoke cases for repair edit-mode comparison."""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from labscriptai.benchmark.authoring_pilot import (
    RepairPatchError,
    _build_protocol_repairer,
    _usage_stats,
    simulate_protocol_file,
)
from labscriptai.benchmark.tasks import AuthoringTask
from labscriptai.runtime.model_adapter import OpenAICompatibleConfig


@dataclass(frozen=True)
class RepairSmokeCase:
    case_id: str
    prompt: str
    protocol_py: str


BROKEN_CASES: tuple[RepairSmokeCase, ...] = (
    RepairSmokeCase(
        case_id="bad_labware",
        prompt="Fix an Opentrons protocol that loads a nonexistent labware name.",
        protocol_py='''metadata = {"protocolName": "bad labware repair smoke", "apiLevel": "2.15"}

def run(protocol):
    plate = protocol.load_labware("not_a_real_96_well_plate", "1")
    protocol.comment(str(plate.wells()[0]))
''',
    ),
    RepairSmokeCase(
        case_id="over_capacity",
        prompt="Fix an Opentrons protocol that aspirates more than the loaded pipette can hold.",
        protocol_py='''metadata = {"protocolName": "over capacity repair smoke", "apiLevel": "2.15"}

def run(protocol):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])
    pipette.pick_up_tip()
    pipette.aspirate(500, reservoir["A1"])
    pipette.dispense(500, plate["A1"])
    pipette.drop_tip()
''',
    ),
    RepairSmokeCase(
        case_id="duplicate_slot",
        prompt="Fix an Opentrons protocol that loads two labware items into the same deck slot.",
        protocol_py='''metadata = {"protocolName": "duplicate slot repair smoke", "apiLevel": "2.15"}

def run(protocol):
    protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    protocol.load_labware("corning_96_wellplate_360ul_flat", "1")
''',
    ),
    RepairSmokeCase(
        case_id="module_misuse",
        prompt="Fix an Opentrons protocol that calls a module method with an invalid argument type.",
        protocol_py='''metadata = {"protocolName": "module misuse repair smoke", "apiLevel": "2.15"}

def run(protocol):
    temp = protocol.load_module("temperature module gen2", "1")
    plate = temp.load_labware("opentrons_96_aluminumblock_generic_pcr_strip_200ul")
    temp.set_temperature("cold")
    protocol.comment(str(plate.wells()[0]))
''',
    ),
)


def _task_for_case(case: RepairSmokeCase) -> AuthoringTask:
    return AuthoringTask(
        task_id=f"REPAIR_{case.case_id}",
        source="repair_smoke",
        difficulty="Hard",
        holdout=True,
        output_contract="protocol.py",
        prompt=case.prompt,
    )


def _changed_lines(before: str, after: str) -> int:
    diff = difflib.ndiff(before.splitlines(), after.splitlines())
    return sum(1 for line in diff if line.startswith(("- ", "+ ")))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_case(
    *,
    case: RepairSmokeCase,
    repair_edit_mode: str,
    output_dir: Path,
    config: OpenAICompatibleConfig,
    opentrons_python: str | None,
    workspace_root: Path | None,
    simulation_timeout_sec: int,
) -> dict[str, Any]:
    case_dir = output_dir / case.case_id / repair_edit_mode
    if case_dir.exists():
        shutil.rmtree(case_dir)
    package_dir = case_dir / "package"
    package_dir.mkdir(parents=True)
    protocol_path = package_dir / "protocol.py"
    protocol_path.write_text(case.protocol_py, encoding="utf-8")

    pre_sim = simulate_protocol_file(
        protocol_path,
        opentrons_python=opentrons_python,
        workspace_root=workspace_root,
        timeout_sec=simulation_timeout_sec,
    )
    record: dict[str, Any] = {
        "case": case.case_id,
        "repair_edit_mode": repair_edit_mode,
        "repair_patch_backend": "diff_edit" if repair_edit_mode == "patch_only" else "rewrite",
        "pre_sim_ok": bool(pre_sim.get("ok")),
        "pre_simulation": pre_sim,
        "post_sim_ok": False,
        "patch_count": 0,
        "patch_rejected_count": 0,
        "changed_lines": 0,
        "full_rewrite_used": repair_edit_mode == "rewrite",
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "error": "",
    }
    if pre_sim.get("ok"):
        record["error"] = "pre-simulation unexpectedly passed; case did not exercise repair"
        _write_json(case_dir / "record.json", record)
        return record

    repairer = _build_protocol_repairer(config, repair_edit_mode)
    try:
        repaired = repairer(_task_for_case(case), case.protocol_py, pre_sim)
        usage = _usage_stats(getattr(repaired, "usage", None))
        record.update(
            {
                "patch_count": int(getattr(repaired, "patch_count", 0)),
                "patch_rejected_count": int(getattr(repaired, "patch_rejected_count", 0)),
                "repair_patch_backend": str(
                    getattr(
                        repaired,
                        "patch_backend",
                        "diff_edit" if repair_edit_mode == "patch_only" else "rewrite",
                    )
                ),
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "total_tokens": usage["total_tokens"],
                "changed_lines": _changed_lines(case.protocol_py, str(repaired)),
            }
        )
        protocol_path.write_text(str(repaired), encoding="utf-8")
        post_sim = simulate_protocol_file(
            protocol_path,
            opentrons_python=opentrons_python,
            workspace_root=workspace_root,
            timeout_sec=simulation_timeout_sec,
        )
        record["post_sim_ok"] = bool(post_sim.get("ok"))
        record["post_simulation"] = post_sim
    except RepairPatchError as exc:
        record["patch_rejected_count"] = int(getattr(exc, "rejected_count", 1))
        usage = _usage_stats(getattr(exc, "usage", None))
        record["input_tokens"] = usage["input_tokens"]
        record["output_tokens"] = usage["output_tokens"]
        record["total_tokens"] = usage["total_tokens"]
        raw_patch = str(getattr(exc, "raw_patch", ""))
        if raw_patch:
            record["raw_patch_tail"] = raw_patch[-4000:]
        record["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # pragma: no cover - live provider and simulator failures.
        usage = _usage_stats(getattr(exc, "usage", None))
        record.update(
            {
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "total_tokens": usage["total_tokens"],
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
    _write_json(case_dir / "record.json", record)
    return record


def _summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_mode.setdefault(str(record["repair_edit_mode"]), []).append(record)
    rows = {}
    for mode, mode_records in by_mode.items():
        rows[mode] = {
            "cases": len(mode_records),
            "pre_sim_failed": sum(not record.get("pre_sim_ok") for record in mode_records),
            "post_sim_passed": sum(bool(record.get("post_sim_ok")) for record in mode_records),
            "patch_count": sum(int(record.get("patch_count", 0)) for record in mode_records),
            "patch_rejected_count": sum(int(record.get("patch_rejected_count", 0)) for record in mode_records),
            "repair_patch_backend": ",".join(
                sorted({str(record.get("repair_patch_backend", "none")) for record in mode_records})
            ),
            "provider_or_repair_errors": sum(bool(record.get("error")) for record in mode_records),
            "tokens": sum(int(record.get("total_tokens", 0)) for record in mode_records),
        }
    return {"rows": rows, "records": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("runs/kb_strong_followup/repair_smoke"))
    parser.add_argument(
        "--repair-edit-mode",
        choices=("rewrite", "patch_only", "both"),
        default="both",
    )
    parser.add_argument("--cases", default="", help="Comma-separated case ids. Defaults to all cases.")
    parser.add_argument("--opentrons-python")
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--simulation-timeout-sec", type=int, default=180)
    args = parser.parse_args()

    selected_ids = {case_id.strip() for case_id in args.cases.split(",") if case_id.strip()}
    selected_cases = [case for case in BROKEN_CASES if not selected_ids or case.case_id in selected_ids]
    missing = selected_ids - {case.case_id for case in BROKEN_CASES}
    if missing:
        raise ValueError(f"unknown repair smoke cases: {', '.join(sorted(missing))}")

    config = OpenAICompatibleConfig.from_env(default_model="deepseek-v4-pro")
    modes = ("rewrite", "patch_only") if args.repair_edit_mode == "both" else (args.repair_edit_mode,)
    records = [
        run_case(
            case=case,
            repair_edit_mode=mode,
            output_dir=args.output_dir,
            config=config,
            opentrons_python=args.opentrons_python,
            workspace_root=args.workspace_root,
            simulation_timeout_sec=args.simulation_timeout_sec,
        )
        for case in selected_cases
        for mode in modes
    ]
    summary = _summarize(records)
    _write_json(args.output_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
