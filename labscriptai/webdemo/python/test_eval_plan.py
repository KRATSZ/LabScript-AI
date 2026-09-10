from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "eval_plan.py"
PYTHONPATH = str(ROOT)

DEMO = {
    "schema": "bpl.plan_ir.lh.v0",
    "plan_id": "demo-transfer",
    "backend": "serializing",
    "resources": [
        {"id": "tips", "type": "tiprack", "slot": "1"},
        {"id": "plate", "type": "plate", "slot": "2", "max_volume_ul": 200},
    ],
    "initial_volumes_ul": {"plate:A1": 100, "plate:B1": 0},
    "steps": [
        {
            "step_id": "1",
            "primitive_type": "PICK_TIPS",
            "tip_rack": "tips",
            "tip_positions": ["A1"],
            "dependencies": [],
        },
        {
            "step_id": "2",
            "primitive_type": "ASPIRATE",
            "source": "plate:A1",
            "volume_ul": 50,
            "dependencies": ["1"],
        },
        {
            "step_id": "3",
            "primitive_type": "DISPENSE",
            "destination": "plate:B1",
            "volume_ul": 50,
            "dependencies": ["2"],
        },
        {
            "step_id": "4",
            "primitive_type": "DROP_TIPS",
            "to_waste": True,
            "dependencies": ["3"],
        },
    ],
}


def run_cli(payload: dict, extra_env: dict[str, str] | None = None) -> dict:
    env = {**os.environ, "PYTHONPATH": PYTHONPATH}
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


class EvalPlanTests(unittest.TestCase):
    def test_validate_only_ok(self) -> None:
        out = run_cli({"plan": DEMO, "validate_only": True})
        self.assertTrue(out["ok"])
        self.assertEqual(out["plan"]["schema"], "bpl.plan_ir.lh.v0")
        self.assertEqual(len(out["plan"]["steps"]), 4)

    def test_validate_only_rejects_bad_schema(self) -> None:
        out = run_cli({"plan": {**DEMO, "schema": "nope"}, "validate_only": True})
        self.assertFalse(out["ok"])
        self.assertTrue(out.get("errors"))

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
        self.assertFalse(out["sim"]["ok"])
        self.assertEqual(out["logicpass"]["outcome"], "skipped")
        self.assertFalse(out["fab"]["lit"])

    def test_checks_never_fake_green_without_plr(self) -> None:
        out = run_cli({"plan": DEMO})
        self.assertIn("sim", out)
        self.assertIn("logicpass", out)
        self.assertFalse(out["fab"]["lit"] and not out["sim"]["ok"])
        if not out["sim"]["ok"]:
            self.assertEqual(out["logicpass"]["outcome"], "skipped")
            self.assertIn(out["sim"].get("reason"), {"plr_unavailable", "sim_failed", "invalid_plan"})

    def test_import_failure_is_not_a_pass(self) -> None:
        out = run_cli({"plan": DEMO}, extra_env={"PYTHONPATH": "/tmp/webdemo-empty-path"})
        self.assertFalse(out["sim"]["ok"])
        self.assertEqual(out["sim"]["reason"], "planir_package_missing")
        self.assertFalse(out["fab"]["lit"])


if __name__ == "__main__":
    unittest.main()
