from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "compile_hamilton.py"
PYTHONPATH = str(ROOT)

DEMO = {
    "schema": "bpl.plan_ir.lh.v0",
    "plan_id": "demo-transfer",
    "protocol_name": "demo-transfer",
    "target": "pylabrobot",
    "backend": "hamilton",
    "resources": [
        {"id": "tips", "type": "tiprack", "slot": "1"},
        {"id": "plate", "type": "plate", "slot": "2", "max_volume_ul": 360},
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


class CompileHamiltonTests(unittest.TestCase):
    def test_min_legal_plan(self) -> None:
        out, _ = run_cli(DEMO)
        self.assertTrue(out["ok"], out)
        script = out["script"]
        self.assertIn("pick_up_tips", script)
        self.assertIn("aspirate", script)
        self.assertIn("dispense", script)
        self.assertIn("drop_tips", script)
        self.assertIn("vols=[50]", script)
        self.assertIn("tips['A1']", script)
        self.assertIn("plate['A1']", script)
        self.assertIn("plate['B1']", script)
        self.assertIn("LiquidHandlerChatterboxBackend", script)
        self.assertIn("# DRY-RUN", script)
        self.assertIn("# backend = VantageBackend()", script)
        self.assertNotIn("\nbackend = VantageBackend()", script)
        self.assertGreaterEqual(out["command_count"], 4)
        self.assertIsInstance(out["warnings"], list)

    def test_mix_cycles_and_wait(self) -> None:
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
        script = out["script"]
        self.assertIn("for _ in range(5):", script)
        self.assertEqual(script.count("await lh.aspirate(plate['A1'], vols=[40])"), 2)
        self.assertIn("await asyncio.sleep(2)", script)
        self.assertEqual(out["command_count"], 1 + 1 + 10 + 1 + 1 + 1)

    def test_bad_plan_is_human(self) -> None:
        out, completed = run_cli("not-json")
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("JSON", out["error"])
        self.assertTrue(out.get("hint"))
        self.assertNotIn("Traceback", completed.stdout)

        out, _ = run_cli({**DEMO, "steps": []})
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("no steps", out["error"].lower())

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


if __name__ == "__main__":
    unittest.main()
