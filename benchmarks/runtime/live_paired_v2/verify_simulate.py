#!/usr/bin/env python3
"""Pre-live acceptance wrapper for live_paired_v2 simulate gate.

Delegates to ``build_bundle.run_simulate_gate`` / ``simulate_protocol`` so P3/P5
(and any other implemented pairs) share one Opentrons simulate path
(``verify_protocol.py`` shim on Python 3.14).
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from benchmarks.runtime.live_paired_v2.build_bundle import (  # noqa: E402
    build_bundle,
    run_simulate_gate,
    simulate_protocol,
)
from benchmarks.runtime.live_paired_v2.common import write_json  # noqa: E402
from benchmarks.runtime.live_paired_v2.pairs import load_pair_module  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=None)
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=["implemented"],
        help="implemented | P1..P6 | module aliases (ignored when --bundle is set)",
    )
    parser.add_argument("--write-report", type=Path, default=None)
    parser.add_argument("--build-temp", action="store_true")
    args = parser.parse_args(argv)

    if args.bundle is not None:
        report = run_simulate_gate(args.bundle / "protocols")
    elif args.build_temp:
        cleanup = Path(tempfile.mkdtemp(prefix="live_paired_v2_sim_"))
        build_bundle(cleanup, force=True, pairs=args.pairs, run_simulate=True)
        report = json.loads((cleanup / "simulate_report.json").read_text(encoding="utf-8"))
    else:
        staging = Path(tempfile.mkdtemp(prefix="live_paired_v2_proto_"))
        from benchmarks.runtime.live_paired_v2.build_bundle import _modules_for_selection

        for mod in _modules_for_selection(args.pairs):
            for case_id, spec in mod.case_specs().items():
                (staging / f"{case_id}.py").write_text(str(spec["protocol_source"]), encoding="utf-8")
        report = run_simulate_gate(staging)

    if args.write_report:
        write_json(args.write_report, report)

    for item in report.get("results") or []:
        status = "PASS" if item.get("ok") else "FAIL"
        print(f"{status} {item.get('protocol')}")

    print(json.dumps(report, indent=2))
    if report.get("skipped"):
        return 3
    return 0 if report.get("simulate_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
