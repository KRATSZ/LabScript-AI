from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "eval_logicpass.py"
PYTHONPATH = str(ROOT)


def run_cli(
    payload: dict,
    extra_env: dict[str, str] | None = None,
    *,
    python: str | None = None,
) -> dict:
    env = {**os.environ, "PYTHONPATH": PYTHONPATH}
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [python or sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


class EvalLogicpassTests(unittest.TestCase):
    def test_missing_analyze_is_unevaluable(self) -> None:
        out = run_cli({})
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])

    def test_invalid_json_exits_zero(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="not-json",
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONPATH": PYTHONPATH},
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        out = json.loads(completed.stdout)
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])

    def test_import_failure_is_unevaluable(self) -> None:
        # Use a non-venv interpreter so editable site-packages do not satisfy import.
        cli_python = shutil.which("python3") or sys.executable
        out = run_cli(
            {},
            extra_env={"PYTHONPATH": "/tmp/webdemo-empty-path"},
            python=cli_python,
        )
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(out["logic_pass"])
        self.assertFalse(out["final_pass_v2"])
        self.assertEqual(out.get("reason"), "logicpass_package_missing")

    def test_fab_projection_never_true_on_unevaluable(self) -> None:
        out = run_cli({})
        lit = (
            bool(out.get("sim_pass"))
            and out.get("outcome") == "pass"
            and out.get("logic_pass") is True
        )
        self.assertEqual(out["outcome"], "unevaluable")
        self.assertFalse(lit)

    def test_package_import_works_from_repo_root(self) -> None:
        sys.path.insert(0, PYTHONPATH)
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        adapter = load_analyze_json(payload={"commands": []}, protocol_path=None)
        result = evaluate_logicpass(sim_pass=True, adapter=adapter)
        payload = result.to_dict()
        self.assertIn(payload["outcome"], {"pass", "fail", "unevaluable"})
        if payload["outcome"] != "pass":
            self.assertFalse(payload["logic_pass"])

    def _overflow_analyze_payload(
        self,
        *,
        volume: float,
        plate_load_name: str | None = "nest_96_wellplate_200ul_flat",
    ) -> dict:
        labware_plate: dict = {"id": "labware-plate"}
        if plate_load_name is not None:
            labware_plate["loadName"] = plate_load_name
        return {
            "commands": [
                {
                    "id": "cmd-pickup",
                    "commandType": "pickUpTip",
                    "status": "succeeded",
                    "params": {
                        "pipetteId": "pipette-left",
                        "labwareId": "labware-tips",
                        "wellName": "A1",
                    },
                },
                {
                    "id": "cmd-dispense",
                    "commandType": "dispense",
                    "status": "succeeded",
                    "params": {
                        "pipetteId": "pipette-left",
                        "labwareId": "labware-plate",
                        "wellName": "B1",
                        "volume": volume,
                    },
                },
            ],
            "labware": [
                {
                    "id": "labware-tips",
                    "loadName": "opentrons_flex_96_tiprack_1000ul",
                },
                labware_plate,
            ],
            "pipettes": [
                {
                    "id": "pipette-left",
                    "pipetteName": "flex_1channel_1000",
                    "mount": "left",
                }
            ],
        }

    def test_dispense_overflow_fails_lp_l4(self) -> None:
        sys.path.insert(0, PYTHONPATH)
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        adapter = load_analyze_json(
            payload=self._overflow_analyze_payload(volume=5000.0)
        )
        result = evaluate_logicpass(sim_pass=True, adapter=adapter)
        payload = result.to_dict()
        issue_codes = [issue["code"] for issue in payload["issues"]]
        self.assertEqual(payload["outcome"], "fail")
        self.assertFalse(payload["logic_pass"])
        self.assertFalse(payload["final_pass_v2"])
        self.assertIn("LP-L4", issue_codes)

    def test_dispense_within_capacity_not_lp_l4_overflow(self) -> None:
        sys.path.insert(0, PYTHONPATH)
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        adapter = load_analyze_json(
            payload=self._overflow_analyze_payload(volume=50.0)
        )
        result = evaluate_logicpass(sim_pass=True, adapter=adapter)
        overflow_issues = [
            issue
            for issue in result.issues
            if issue.code == "LP-L4" and issue.severity == "error"
        ]
        self.assertEqual(overflow_issues, [])

    def test_dispense_without_capacity_hint_is_not_pass(self) -> None:
        sys.path.insert(0, PYTHONPATH)
        from labscriptai.benchmark.logicpass import evaluate_logicpass, load_analyze_json

        adapter = load_analyze_json(
            payload=self._overflow_analyze_payload(
                volume=5000.0, plate_load_name=None
            )
        )
        result = evaluate_logicpass(sim_pass=True, adapter=adapter)
        payload = result.to_dict()
        self.assertNotEqual(payload["outcome"], "pass")
        self.assertFalse(payload["logic_pass"])
        self.assertFalse(payload["final_pass_v2"])


if __name__ == "__main__":
    unittest.main()
