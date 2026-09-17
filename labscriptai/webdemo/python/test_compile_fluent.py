from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parent / "compile_fluent.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "igem_fluorescein_plan.json"
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


def gwl_ops(gwl: str) -> list[str]:
    return [line for line in gwl.splitlines() if line.startswith(("A;", "D;", "W;"))]


def assert_adw(ops: list[str]) -> None:
    """FluentControl: A; D; W; repeating. Never B;."""
    assert ops, "expected A/D/W lines"
    assert "B;" not in ops
    assert len(ops) % 3 == 0, ops
    for i in range(0, len(ops), 3):
        assert ops[i].startswith("A;"), ops[i : i + 3]
        assert ops[i + 1].startswith("D;"), ops[i : i + 3]
        assert ops[i + 2] == "W;", ops[i : i + 3]


def pick_mix_drop(*, cycles: int | None = 3, volume_ul: float | None = 40) -> dict:
    mix: dict = {
        "step_id": "2",
        "primitive_type": "MIX",
        "location": "plate:A1",
        "dependencies": ["1"],
    }
    if volume_ul is not None:
        mix["volume_ul"] = volume_ul
    if cycles is not None:
        mix["cycles"] = cycles
    return {
        **DEMO,
        "steps": [
            DEMO["steps"][0],
            mix,
            DEMO["steps"][3] | {"step_id": "3", "dependencies": ["2"]},
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
        self.assertIn("\nW;\n", "\n" + gwl if not gwl.startswith("W;") else gwl)
        self.assertNotIn("B;", gwl)
        assert_adw(gwl_ops(gwl))
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

    def test_tip_positions_with_resource_prefix(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                {**DEMO["steps"][0], "tip_positions": ["TIPS:A1"]},
                *DEMO["steps"][1:],
            ],
        }
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"], out)
        gwl = out["worklist_gwl"]
        self.assertNotIn("IPS", gwl)
        self.assertIn("A;plate;;;A1;;50;Water Free Single;;1;", gwl)
        self.assertIn("D;plate;;;B1;;50;Water Free Single;;1;", gwl)

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
        gwl = out["worklist_gwl"]
        self.assertIn("MIX steps are expanded to aspirate/dispense/W cycles", gwl)
        mix_unit = [
            "A;plate;;;A1;;40;Water Free Single;;1;",
            "D;plate;;;A1;;40;Water Free Single;;1;",
            "W;",
        ]
        ops = gwl_ops(gwl)
        self.assertEqual(ops[:15], mix_unit * 5)
        self.assertEqual(
            ops[15:],
            [
                "A;plate;;;A1;;40;Water Free Single;;1;",
                "D;plate;;;B1;;40;Water Free Single;;1;",
                "W;",
            ],
        )
        assert_adw(ops)
        self.assertNotIn("B;", gwl)
        self.assertTrue(any("WAIT" in line for line in gwl.splitlines()))
        joined = " ".join(out["warnings"]).lower()
        self.assertNotIn("mix not supported", joined)
        self.assertFalse(any("mix" in w.lower() and "worklist" in w.lower() for w in out["warnings"]))
        self.assertIn("wait", joined)
        # XML already includes AddLabware; MIX's 1 LihaMix is replaced by 10 A/D.
        self.assertEqual(out["command_count"], 6 + 9)

    def test_mix_cycle_bounds(self) -> None:
        out1, _ = run_cli(pick_mix_drop(cycles=1, volume_ul=25))
        self.assertTrue(out1["ok"], out1)
        ops1 = gwl_ops(out1["worklist_gwl"])
        self.assertEqual(
            ops1,
            [
                "A;plate;;;A1;;25;Water Free Single;;1;",
                "D;plate;;;A1;;25;Water Free Single;;1;",
                "W;",
            ],
        )
        self.assertEqual(out1["command_count"], 1 + 1 + 2 + 1)  # AddLabware + pick + A/D + drop
        self.assertIn("LihaMixScriptCommandDataV4", out1["script_xml"])

        out5, _ = run_cli(pick_mix_drop(cycles=5, volume_ul=25))
        self.assertTrue(out5["ok"], out5)
        ops5 = gwl_ops(out5["worklist_gwl"])
        unit = [
            "A;plate;;;A1;;25;Water Free Single;;1;",
            "D;plate;;;A1;;25;Water Free Single;;1;",
            "W;",
        ]
        self.assertEqual(ops5, unit * 5)
        self.assertEqual(out5["command_count"], 1 + 1 + 10 + 1)

        out_default, _ = run_cli(pick_mix_drop(cycles=None, volume_ul=25))
        self.assertTrue(out_default["ok"], out_default)
        self.assertEqual(len(gwl_ops(out_default["worklist_gwl"])), 9)  # 3 cycles × A/D/W

    def test_mix_w_terminates_ad(self) -> None:
        plan = {
            **DEMO,
            "steps": [
                DEMO["steps"][0],
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
                    "primitive_type": "MIX",
                    "location": "plate:B1",
                    "volume_ul": 50,
                    "cycles": 2,
                    "dependencies": ["3"],
                },
                {
                    "step_id": "5",
                    "primitive_type": "ASPIRATE",
                    "source": "plate:B1",
                    "volume_ul": 50,
                    "dependencies": ["4"],
                },
                {
                    "step_id": "6",
                    "primitive_type": "DISPENSE",
                    "destination": "plate:B2",
                    "volume_ul": 50,
                    "dependencies": ["5"],
                },
                DEMO["steps"][3] | {"step_id": "7", "dependencies": ["6"]},
            ],
        }
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"], out)
        ops = gwl_ops(out["worklist_gwl"])
        self.assertEqual(
            ops,
            [
                "A;plate;;;A1;;50;Water Free Single;;1;",
                "D;plate;;;B1;;50;Water Free Single;;1;",
                "W;",
                "A;plate;;;B1;;50;Water Free Single;;1;",
                "D;plate;;;B1;;50;Water Free Single;;1;",
                "W;",
                "A;plate;;;B1;;50;Water Free Single;;1;",
                "D;plate;;;B1;;50;Water Free Single;;1;",
                "W;",
                "A;plate;;;B1;;50;Water Free Single;;1;",
                "D;plate;;;B2;;50;Water Free Single;;1;",
                "W;",
            ],
        )
        self.assertEqual(ops.count("W;"), 4)
        self.assertEqual(ops[-1], "W;")
        self.assertNotIn("B;", out["worklist_gwl"])
        self.assertFalse(any("mix" in w.lower() for w in out["warnings"]))

    def test_mix_missing_volume(self) -> None:
        out, completed = run_cli(pick_mix_drop(cycles=3, volume_ul=None))
        self.assertFalse(out["ok"])
        self.assertEqual(out["stage"], "mapping")
        self.assertIn("volume_ul", out["error"])
        self.assertIn("MIX", out["error"])
        self.assertTrue(out.get("hint"))
        self.assertNotIn("Traceback", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)

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
        assert_adw(gwl_ops(gwl))
        self.assertNotIn("B;", gwl)
        self.assertIn("SelectedWellsString>A1,B1<", out["script_xml"])
        self.assertIn("SelectedWellsString>C1,D1<", out["script_xml"])

    def test_over_max_volume_fails(self) -> None:
        plan = {**DEMO, "initial_volumes_ul": {"plate:A1": 500}}
        out, _ = run_cli(plan)
        self.assertFalse(out["ok"])
        self.assertEqual(out.get("stage"), "mapping")
        self.assertIn("max_volume", out.get("error") or "")

    def test_invalid_tip_well_z9_fails(self) -> None:
        steps = list(DEMO["steps"])
        steps[0] = {**steps[0], "tip_positions": ["Z9"]}
        plan = {**DEMO, "steps": steps}
        out, _ = run_cli(plan)
        self.assertFalse(out["ok"])
        self.assertEqual(out.get("stage"), "mapping")
        self.assertIn("Z9", out.get("error") or "")

    def test_igem_fluorescein_gold_fixture(self) -> None:
        plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
        out, _ = run_cli(plan)
        self.assertTrue(out["ok"], out)
        gwl = out["worklist_gwl"]
        for row in "ABCD":
            self.assertNotIn(f"A;plate;;;{row}12;;", gwl)
            self.assertIn(f"D;plate;;;{row}12;;100;", gwl)
        self.assertIn("D;waste;;;A1;;100;", gwl)
        ops = gwl_ops(gwl)
        assert_adw(ops)
        self.assertNotIn("B;", gwl)
        mix_a2 = [
            line
            for line in ops
            if line.startswith(("A;plate;;;A2;;100;", "D;plate;;;A2;;100;"))
        ]
        # MIX col2 = 3 cycles × A+D; plus PBS D and transfer D.
        self.assertGreaterEqual(len(mix_a2), 6)


if __name__ == "__main__":
    unittest.main()
