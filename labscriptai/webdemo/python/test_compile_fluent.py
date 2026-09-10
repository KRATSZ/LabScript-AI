from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "compile_fluent.py"
PYTHONPATH = str(ROOT)

DEMO = {
    "schema": "bpl.plan_ir.lh.v0",
    "plan_id": "demo-transfer",
    "protocol_name": "demo-transfer",
    "target": "pylabrobot",
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


def run_cli(payload: dict | str) -> tuple[dict, subprocess.CompletedProcess[str]]:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=raw,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": PYTHONPATH},
        check=False,
    )
    try:
        out = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"stdout was not JSON (exit {completed.returncode}): {completed.stdout!r}\nstderr={completed.stderr}"
        ) from exc
    expected = 0 if out.get("ok") else 1
    assert completed.returncode == expected, (
        f"exit {completed.returncode} != {expected} for ok={out.get('ok')}: {out}\nstderr={completed.stderr}"
    )
    return out, completed


class CompileFluentTests(unittest.TestCase):
    def test_min_legal_plan(self) -> None:
        out, _ = run_cli(DEMO)
        self.assertTrue(out["ok"])
        gwl = out["worklist_gwl"]
        xml = out["script_xml"]
        self.assertIn("A;plate;;;A1;;50;Water Free Single;;1;", gwl)
        self.assertIn("D;plate;;;B1;;50;Water Free Single;;1;", gwl)
        self.assertIn("\nB;\n", "\n" + gwl if not gwl.startswith("B;") else gwl)
        self.assertTrue(any(line.strip() == "B;" for line in gwl.splitlines()))
        self.assertIn("LihaGetTipsScriptCommandDataV3", xml)
        self.assertIn("LihaAspirateScriptCommandDataV5", xml)
        self.assertIn("LihaDispenseScriptCommandDataV6", xml)
        self.assertIn("LihaDropTipsScriptCommandDataV2", xml)
        self.assertGreaterEqual(out["command_count"], 4)
        self.assertIsInstance(out["warnings"], list)

    def test_aspirate_without_tips_is_state_machine(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                {
                    "step_id": "1",
                    "primitive_type": "ASPIRATE",
                    "source": "plate:A1",
                    "volume_ul": 50,
                    "dependencies": [],
                }
            ],
        }
        out, completed = run_cli(plan)
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "state_machine")
        self.assertIn("PICK_TIPS", out["error"])
        self.assertIn("no tips", out["error"].lower())
        self.assertTrue(out.get("hint"))
        self.assertNotIn("Traceback", completed.stdout)

    def test_empty_steps(self) -> None:
        out, _ = run_cli({**DEMO, "steps": []})
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("no steps", out["error"].lower())

    def test_bad_json(self) -> None:
        out, completed = run_cli("not-json")
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("JSON", out["error"])
        self.assertNotIn("Traceback", completed.stdout)
        self.assertIn("hint", out)

    def test_missing_resource_ref(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                DEMO["steps"][0],
                {
                    "step_id": "2",
                    "primitive_type": "ASPIRATE",
                    "source": "missing:A1",
                    "volume_ul": 50,
                    "dependencies": ["1"],
                },
            ],
        }
        out, _ = run_cli(plan)
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("missing", out["error"])
        self.assertIn("resources", out["error"].lower())

    def test_mix_and_wait(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                DEMO["steps"][0],
                {
                    "step_id": "2",
                    "primitive_type": "ASPIRATE",
                    "source": "plate:A1",
                    "volume_ul": 40,
                    "dependencies": ["1"],
                },
                {
                    "step_id": "3",
                    "primitive_type": "MIX",
                    "location": "plate:A1",
                    "volume_ul": 40,
                    "cycles": 5,
                    "dependencies": ["2"],
                },
                {
                    "step_id": "4",
                    "primitive_type": "WAIT",
                    "duration_s": 2,
                    "dependencies": ["3"],
                },
                {
                    "step_id": "5",
                    "primitive_type": "DISPENSE",
                    "destination": "plate:B1",
                    "volume_ul": 40,
                    "dependencies": ["4"],
                },
                DEMO["steps"][3] | {"step_id": "6", "dependencies": ["5"]},
            ],
        }
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"], out)
        self.assertIn("LihaMixScriptCommandDataV4", out["script_xml"])
        self.assertTrue(any(line.startswith("C; MIX") for line in out["worklist_gwl"].splitlines()))
        self.assertTrue(any("WAIT" in line for line in out["worklist_gwl"].splitlines()))
        joined = " ".join(out["warnings"]).lower()
        self.assertIn("mix", joined)
        self.assertIn("wait", joined)

    def test_multiwell_expands(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                {
                    "step_id": "1",
                    "primitive_type": "PICK_TIPS",
                    "tip_rack": "tips",
                    "tip_positions": ["A1", "B1"],
                    "dependencies": [],
                },
                {
                    "step_id": "2",
                    "primitive_type": "ASPIRATE",
                    "source": ["plate:A1", "plate:B1"],
                    "volume_ul": 25,
                    "dependencies": ["1"],
                },
                {
                    "step_id": "3",
                    "primitive_type": "DISPENSE",
                    "destination": ["plate:C1", "plate:D1"],
                    "volume_ul": 25,
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
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"], out)
        gwl = out["worklist_gwl"]
        self.assertIn("A;plate;;;A1;;25;Water Free Single;;1;", gwl)
        self.assertIn("A;plate;;;B1;;25;Water Free Single;;2;", gwl)
        self.assertIn("D;plate;;;C1;;25;Water Free Single;;1;", gwl)
        self.assertIn("D;plate;;;D1;;25;Water Free Single;;2;", gwl)
        self.assertIn("SelectedWellsString>A1,B1<", out["script_xml"])
        self.assertIn("SelectedWellsString>C1,D1<", out["script_xml"])

    def test_over_max_volume_warns(self) -> None:
        plan = {**DEMO, "initial_volumes_ul": {"plate:A1": 500}}
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"])
        self.assertTrue(any("max_volume" in w for w in out["warnings"]))


if __name__ == "__main__":
    unittest.main()
