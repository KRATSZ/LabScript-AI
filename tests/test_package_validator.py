from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.benchmark.package_validator import (
    LEGACY_PACKAGE_FILES,
    REQUIRED_PACKAGE_FILES,
    THREE_PIECE_PACKAGE_FILES,
    validate_package,
)
from labscriptai.benchmark.score_record import score_record_from_validation


def write_valid_package(root: Path) -> None:
    (root / "protocol.py").write_text(
        'metadata = {"protocolName": "benchmark smoke"}\n'
        "def run(protocol):\n"
        "    pass\n",
        encoding="utf-8",
    )
    (root / "deck_plan.json").write_text(
        json.dumps(
            {
                "labware": [
                    {"name": "opentrons_96_wellplate_200ul_pcr_full_skirt", "slot": "D1"},
                    {"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"},
                ],
                "modules": [],
                "instruments": [{"name": "flex_1channel_1000", "mount": "left"}],
            }
        ),
        encoding="utf-8",
    )
    (root / "reagent_plan.json").write_text(
        json.dumps(
            {
                "reagents": [
                    {
                        "name": "water",
                        "source": "reservoir:A1",
                        "required_volume_ul": 900,
                        "available_volume_ul": 1200,
                        "dead_volume_ul": 100,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "tip_plan.json").write_text(
        json.dumps({"tips_required": 8, "tips_available": 96, "policy": "one_tip_per_sample"}),
        encoding="utf-8",
    )
    (root / "runbook.md").write_text("# Setup\nLoad the listed labware and reagents.\n", encoding="utf-8")
    (root / "risk_checklist.json").write_text(
        json.dumps({"critical_failures": [], "manual_checks": ["confirm liquid levels"]}),
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "task_id": "T056",
                "system_id": "labscriptai",
                "model_id": "test-model",
                "scaffold_id": "LabscriptAI",
                "prompt_hash": "abc123",
                "retry_budget": {
                    "max_attempts": 8,
                    "max_wall_time_sec": 1800,
                    "max_output_tokens": 24000,
                    "max_tool_calls": 80,
                },
                "tool_permissions": ["simulate_protocol"],
                "timestamp": "2026-05-13T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )


def write_valid_three_piece_package(root: Path) -> None:
    (root / "protocol.py").write_text(
        'metadata = {"protocolName": "benchmark smoke"}\n'
        "def run(protocol):\n"
        "    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A1')\n"
        "    protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', 'D1')\n"
        "    protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])\n",
        encoding="utf-8",
    )
    (root / "setup_card.html").write_text(
        "<h1>Setup</h1><table><tr><td>D1</td><td>plate</td></tr></table>\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "0.4",
                "task_id": "T056",
                "system_id": "labscriptai",
                "model_id": "test-model",
                "scaffold_id": "LabscriptAI",
                "prompt_hash": "abc123",
                "deck": {
                    "slots": [
                        {"name": "opentrons_96_wellplate_200ul_pcr_full_skirt", "slot": "D1"},
                        {"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"},
                    ],
                    "modules": [],
                    "instruments": [{"name": "flex_1channel_1000", "mount": "left"}],
                },
                "reagents": [
                    {
                        "name": "water",
                        "source": "reservoir:A1",
                        "required_volume_ul": 900,
                        "available_volume_ul": 1200,
                        "dead_volume_ul": 100,
                    }
                ],
                "tips": {"tips_required": 8, "tips_available": 96},
                "risk_flags": ["confirm liquid levels"],
                "critical_failures": [],
                "off_platform_handoff": {"declared": False},
                "tool_permissions": ["simulate_protocol"],
                "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
                "timestamp": "2026-05-13T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )


class PackageValidatorTests(unittest.TestCase):
    def test_three_piece_package_passes_when_simulation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_three_piece_package(root)

            result = validate_package(root, simulation_pass=True)

            self.assertTrue(result.ok)
            self.assertEqual(result.package_complete, True)
            self.assertEqual(result.critical_failures, ())
            self.assertEqual(result.deck_consistency_score, 1.0)
            self.assertEqual(result.volume_feasibility_score, 1.0)
            self.assertEqual(result.tip_budget_score, 1.0)
            self.assertEqual(result.risk_flag_recall, 1.0)
            self.assertEqual(result.handoff_declared_score, 1.0)
            self.assertEqual(REQUIRED_PACKAGE_FILES, THREE_PIECE_PACKAGE_FILES)

    def test_legacy_package_still_uses_seven_file_reader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)

            result = validate_package(root, simulation_pass=True)

            self.assertTrue(result.ok)
            self.assertEqual(len(LEGACY_PACKAGE_FILES), 7)

    def test_valid_package_passes_when_simulation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)

            result = validate_package(root, simulation_pass=True)

            self.assertTrue(result.ok)
            self.assertEqual(result.package_complete, True)
            self.assertEqual(result.critical_failures, ())
            self.assertEqual(result.deck_consistency_score, 1.0)
            self.assertEqual(result.volume_feasibility_score, 1.0)
            self.assertEqual(result.tip_budget_score, 1.0)
            self.assertEqual(result.risk_flag_recall, 1.0)
            self.assertEqual(result.handoff_declared_score, 1.0)

    def test_missing_file_is_schema_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "runbook.md").unlink()

            result = validate_package(root, simulation_pass=True)

            self.assertFalse(result.ok)
            self.assertFalse(result.package_complete)
            self.assertIn("schema_invalid", result.critical_failures)
            self.assertEqual(len(LEGACY_PACKAGE_FILES), 7)

    def test_reagent_underfill_and_tip_exhaustion_are_critical_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "reagent_plan.json").write_text(
                json.dumps(
                    {
                        "reagents": [
                            {
                                "name": "master_mix",
                                "required_volume_ul": 1000,
                                "available_volume_ul": 900,
                                "dead_volume_ul": 50,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (root / "tip_plan.json").write_text(
                json.dumps({"tips_required": 120, "tips_available": 96}),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

            self.assertFalse(result.ok)
            self.assertIn("reagent_underfill", result.critical_failures)
            self.assertIn("tip_exhaustion", result.critical_failures)
            self.assertEqual(result.volume_feasibility_score, 0.0)
            self.assertEqual(result.tip_budget_score, 0.0)

    def test_zero_available_reagent_volume_is_underfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "reagent_plan.json").write_text(
                json.dumps(
                    {
                        "reagents": [
                            {
                                "name": "water",
                                "required_volume_ul": 10,
                                "available_volume_ul": 0,
                                "dead_volume_ul": 0,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

            self.assertFalse(result.ok)
        self.assertIn("reagent_underfill", result.critical_failures)

    def test_deck_plan_must_match_protocol_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "protocol.py").write_text(
                'metadata = {"protocolName": "deck mismatch"}\n'
                "def run(protocol):\n"
                "    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A1')\n"
                "    plate = protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', 'D1')\n"
                "    protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])\n",
                encoding="utf-8",
            )
            (root / "deck_plan.json").write_text(
                json.dumps(
                    {
                        "labware": [
                            {"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"},
                        ],
                        "instruments": [],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("deck_conflict", result.critical_failures)

    def test_tip_plan_requires_explicit_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "tip_plan.json").write_text(
                json.dumps({"policy": "fresh_tip_each_transfer"}),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_tip_plan_accepts_nested_tiprack_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "tip_plan.json").write_text(
                json.dumps(
                    {
                        "tip_racks": [
                            {
                                "labware": "opentrons_96_tiprack_300ul",
                                "tips_used": ["A1", "A2"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_tip_plan_accepts_nested_tips_object_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "tip_plan.json").write_text(
                json.dumps(
                    {
                        "tips": {
                            "tips_required": 3,
                            "tips_available": 96,
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_deck_plan_accepts_named_mapping_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "protocol.py").write_text(
                'metadata = {"protocolName": "mapping deck"}\n'
                "def run(protocol):\n"
                "    protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', location='D1')\n"
                "    protocol.load_instrument('flex_1channel_1000', mount='left')\n",
                encoding="utf-8",
            )
            (root / "deck_plan.json").write_text(
                json.dumps(
                    {
                        "labware": {
                            "plate": {
                                "name": "opentrons_96_wellplate_200ul_pcr_full_skirt",
                                "location": "D1",
                            }
                        },
                        "pipettes": {
                            "left": {"name": "flex_1channel_1000", "mount": "left"}
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_deck_plan_accepts_definition_key_and_integer_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "protocol.py").write_text(
                'metadata = {"protocolName": "deck aliases"}\n'
                "def run(protocol):\n"
                "    protocol.load_labware('corning_96_wellplate_360ul_flat', '2')\n"
                "    protocol.load_instrument('p300_single_gen2', 'left')\n",
                encoding="utf-8",
            )
            (root / "deck_plan.json").write_text(
                json.dumps(
                    {
                        "labware": [
                            {"definition": "corning_96_wellplate_360ul_flat", "slot": 2}
                        ],
                        "instruments": [
                            {"name": "p300_single_gen2", "type": "single channel", "mount": "left"}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_risk_checklist_requires_critical_failures_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "risk_checklist.json").write_text(
                json.dumps({"risk_checklist": []}),
                encoding="utf-8",
            )

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_risk_flag_recall_scores_expected_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "risk_checklist.json").write_text(
                json.dumps(
                    {
                        "critical_failures": [],
                        "risk_flags": [
                            "post-PCR contamination boundary",
                            {"flag": "enzyme warm time"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(
                root,
                simulation_pass=True,
                expected_risk_flags=[
                    "post-PCR contamination boundary",
                    "enzyme warm time",
                    "cold chain",
                ],
            )

        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.risk_flag_recall, 2 / 3)

    def test_expected_off_platform_handoff_must_be_declared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)

            missing = validate_package(
                root,
                simulation_pass=True,
                expected_handoffs=["plate_reader"],
            )
            self.assertFalse(missing.ok)
            self.assertEqual(missing.handoff_declared_score, 0.0)
            self.assertIn("schema_invalid", missing.critical_failures)

            (root / "risk_checklist.json").write_text(
                json.dumps(
                    {
                        "critical_failures": [],
                        "off_platform_handoffs": ["plate_reader"],
                    }
                ),
                encoding="utf-8",
            )

            declared = validate_package(
                root,
                simulation_pass=True,
                expected_handoffs=["plate_reader"],
            )

        self.assertTrue(declared.ok)
        self.assertEqual(declared.handoff_declared_score, 1.0)

    def test_task_manifest_merges_expected_risk_flags(self) -> None:
        manifest_path = ROOT / "benchmarks" / "authoring" / "tasks.yaml"
        if not manifest_path.exists():
            self.skipTest("benchmarks/authoring/tasks.yaml not present")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "manifest.json").write_text(
                json.dumps(
                    {
                        "task_id": "T064",
                        "system_id": "labscriptai",
                        "model_id": "test-model",
                        "scaffold_id": "LabscriptAI",
                        "prompt_hash": "abc123",
                        "retry_budget": {
                            "max_attempts": 8,
                            "max_wall_time_sec": 1800,
                            "max_output_tokens": 24000,
                            "max_tool_calls": 80,
                        },
                        "tool_permissions": ["simulate_protocol"],
                        "timestamp": "2026-05-13T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            (root / "risk_checklist.json").write_text(
                json.dumps(
                    {
                        "critical_failures": [],
                        "risk_flags": ["control placement declared"],
                    }
                ),
                encoding="utf-8",
            )

            result = validate_package(
                root,
                simulation_pass=True,
                task_manifest_path=manifest_path,
            )

        self.assertTrue(result.ok)
        self.assertAlmostEqual(result.risk_flag_recall, 0.5)

    def test_score_record_uses_validation_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            result = validate_package(root, simulation_pass=True)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

            score = score_record_from_validation(
                result,
                manifest,
                first_pass=True,
                attempts=1,
                wall_time_sec=2.5,
                input_tokens=10,
                output_tokens=20,
            ).to_dict()

            self.assertTrue(score["first_pass_success"])
            self.assertTrue(score["best_of_budget_success"])
            self.assertEqual(score["task_id"], "T056")
            self.assertEqual(score["critical_failures"], [])


if __name__ == "__main__":
    unittest.main()
