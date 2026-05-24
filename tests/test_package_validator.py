from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.benchmark.package_validator import (
    REQUIRED_PACKAGE_FILES,
    THREE_PIECE_PACKAGE_FILES,
    validate_package,
)
from labscriptai.benchmark.score_record import score_record_from_validation


def write_valid_package(root: Path) -> None:
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
    write_manifest(root)


def write_manifest(root: Path, **updates: object) -> None:
    manifest: dict[str, object] = {
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
    manifest.update(updates)
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class PackageValidatorTests(unittest.TestCase):
    def test_three_piece_package_passes_when_simulation_passes(self) -> None:
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
        self.assertEqual(REQUIRED_PACKAGE_FILES, THREE_PIECE_PACKAGE_FILES)

    def test_legacy_seven_file_package_fails_without_v04_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "protocol.py").write_text("def run(protocol):\n    pass\n", encoding="utf-8")
            old_plan_files = [f"{stem}_plan.json" for stem in ("deck", "reagent", "tip")]
            old_plan_files.append("risk_" + "checklist.json")
            for name in old_plan_files:
                (root / name).write_text("{}", encoding="utf-8")
            (root / ("runbook" + ".md")).write_text("# Setup\n", encoding="utf-8")

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertFalse(result.package_complete)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_missing_setup_card_is_schema_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "setup_card.html").unlink()

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertFalse(result.package_complete)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_reagent_underfill_and_tip_exhaustion_are_critical_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            write_manifest(
                root,
                reagents=[
                    {
                        "name": "master_mix",
                        "required_volume_ul": 1000,
                        "available_volume_ul": 900,
                        "dead_volume_ul": 50,
                    }
                ],
                tips={"tips_required": 120, "tips_available": 96},
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
            write_manifest(
                root,
                reagents=[
                    {
                        "name": "water",
                        "required_volume_ul": 10,
                        "available_volume_ul": 0,
                        "dead_volume_ul": 0,
                    }
                ],
            )

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("reagent_underfill", result.critical_failures)

    def test_manifest_deck_must_match_protocol_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            (root / "protocol.py").write_text(
                'metadata = {"protocolName": "deck mismatch"}\n'
                "def run(protocol):\n"
                "    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A1')\n"
                "    protocol.load_labware('opentrons_96_wellplate_200ul_pcr_full_skirt', 'D1')\n"
                "    protocol.load_instrument('flex_1channel_1000', 'left', tip_racks=[tiprack])\n",
                encoding="utf-8",
            )
            write_manifest(
                root,
                deck={
                    "slots": [{"name": "opentrons_flex_96_tiprack_200ul", "slot": "A1"}],
                    "instruments": [],
                },
            )

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("deck_conflict", result.critical_failures)

    def test_manifest_tips_require_explicit_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            write_manifest(root, tips={"policy": "fresh_tip_each_transfer"})

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_manifest_accepts_nested_tiprack_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            write_manifest(
                root,
                tips={
                    "tip_racks": [
                        {"labware": "opentrons_96_tiprack_300ul", "tips_used": ["A1", "A2"]}
                    ]
                },
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_manifest_accepts_named_mapping_sections(self) -> None:
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
            write_manifest(
                root,
                deck={
                    "labware": {
                        "plate": {
                            "name": "opentrons_96_wellplate_200ul_pcr_full_skirt",
                            "location": "D1",
                        }
                    },
                    "pipettes": {"left": {"name": "flex_1channel_1000", "mount": "left"}},
                },
            )

            result = validate_package(root, simulation_pass=True)

        self.assertTrue(result.ok)

    def test_risk_fields_require_critical_failures_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            write_manifest(root, critical_failures="none")

            result = validate_package(root, simulation_pass=True)

        self.assertFalse(result.ok)
        self.assertIn("schema_invalid", result.critical_failures)

    def test_risk_flag_recall_scores_expected_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_package(root)
            write_manifest(
                root,
                risk_flags=[
                    "post-PCR contamination boundary",
                    {"flag": "enzyme warm time"},
                ],
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

            write_manifest(root, off_platform_handoffs=["plate_reader"])

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
            write_manifest(root, task_id="T064", risk_flags=["control placement declared"])

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
