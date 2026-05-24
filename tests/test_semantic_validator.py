from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.benchmark.semantic_validator import (
    validate_param_sweep,
    validate_semantics,
)
from labscriptai.benchmark.tasks import AuthoringTask, TaskReagentSpec, TaskSpec
from tests.test_package_validator import write_valid_package


class SemanticValidatorTests(unittest.TestCase):
    def test_flags_missing_negative_control(self) -> None:
        task = AuthoringTask(
            task_id="T900",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Set up qPCR with a negative control and 10uL reactions.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)

            result = validate_semantics(package_dir, task)

        self.assertFalse(result.ok)
        self.assertIn("missing_negative_control", [issue.code for issue in result.issues])

    def test_accepts_declared_controls_and_volumes(self) -> None:
        task = AuthoringTask(
            task_id="T901",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Set up qPCR with a negative control and 10uL reactions.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "runbook.md").write_text(
                "# Setup\nInclude a negative control. Use 10uL reactions.\n",
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.ok)
        self.assertTrue(result.checks["negative_control_present"])
        self.assertTrue(result.checks["prompt_volume_coverage"])

    def test_flags_tip_count_below_sample_count(self) -> None:
        task = AuthoringTask(
            task_id="T902",
            source="test",
            difficulty="Medium",
            holdout=False,
            output_contract="execution_package",
            prompt="Transfer with one fresh tip per sample for 24 samples.",
            spec=TaskSpec(default_samples=24),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "tip_plan.json").write_text(
                '{"tips_required": 8, "tips_available": 96}',
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertFalse(result.ok)
        self.assertIn("tip_count_below_sample_count", [issue.code for issue in result.issues])

    def test_accepts_nested_tip_counts_over_top_level_placeholder(self) -> None:
        task = AuthoringTask(
            task_id="T906",
            source="test",
            difficulty="Medium",
            holdout=False,
            output_contract="execution_package",
            prompt="Transfer with one fresh tip per sample for 24 samples.",
            spec=TaskSpec(default_samples=24),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "tip_plan.json").write_text(
                """
                {
                  "tips_required": 1,
                  "tips_available": 96,
                  "tip_plan": {"total_tips_required": 24},
                  "pipettes": {
                    "p20_single_gen2": {"tips_used": 24, "tips_available": 96}
                  }
                }
                """,
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["tip_count_covers_samples"])
        self.assertNotIn("tip_count_below_sample_count", [issue.code for issue in result.issues])

    def test_accepts_tip_racks_as_dict(self) -> None:
        task = AuthoringTask(
            task_id="T907",
            source="test",
            difficulty="Medium",
            holdout=False,
            output_contract="execution_package",
            prompt="Transfer with one fresh tip per sample for 24 samples.",
            spec=TaskSpec(default_samples=24),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "tip_plan.json").write_text(
                """
                {
                  "tip_racks": {
                    "slot_4": {
                      "labware": "opentrons_96_tiprack_20ul",
                      "tips_used": 24
                    }
                  }
                }
                """,
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["tip_count_covers_samples"])

    def test_flags_waste_capacity_below_expected_waste(self) -> None:
        task = AuthoringTask(
            task_id="T903",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Wash 96 wells with 600 uL per well and discard into liquid waste.",
            spec=TaskSpec(
                default_samples=96,
                reagents=(
                    TaskReagentSpec(
                        name="wash_buffer",
                        volume_per_sample_uL=600,
                        source="reservoir_slot_2",
                    ),
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "runbook.md").write_text(
                "# Setup\nWaste container max fill capacity: 50 mL.\n",
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertFalse(result.ok)
        self.assertIn("waste_capacity_insufficient", [issue.code for issue in result.issues])

    def test_generic_discard_needs_route_but_not_fixed_trash_liters(self) -> None:
        task = AuthoringTask(
            task_id="T905",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Discard used tips into fixed trash after each transfer.",
            spec=TaskSpec(default_samples=8),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "runbook.md").write_text(
                "# Setup\nUsed tips go to the fixed trash bin after each transfer.\n",
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["waste_route_declared"])
        self.assertTrue(result.checks["waste_capacity_declared"])
        self.assertNotIn("waste_capacity_missing", [issue.code for issue in result.issues])

    def test_accepts_matching_reagent_totals(self) -> None:
        task = AuthoringTask(
            task_id="T904",
            source="test",
            difficulty="Medium",
            holdout=False,
            output_contract="execution_package",
            prompt="Dispense buffer with one fresh tip per sample.",
            spec=TaskSpec(
                default_samples=8,
                reagents=(
                    TaskReagentSpec(
                        name="water",
                        volume_per_sample_uL=100,
                        source="reservoir_slot_2",
                    ),
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["reagent_totals_match_task_spec"])

    def test_accepts_reagent_dict_aliases_and_names(self) -> None:
        task = AuthoringTask(
            task_id="T908",
            source="test",
            difficulty="Medium",
            holdout=False,
            output_contract="execution_package",
            prompt="Dispense qPCR master mix and template_or_control.",
            spec=TaskSpec(
                default_samples=24,
                reagents=(
                    TaskReagentSpec(name="qpcr_master_mix", volume_per_sample_uL=10),
                    TaskReagentSpec(name="template_or_control", volume_per_sample_uL=5),
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "reagent_plan.json").write_text(
                """
                {
                  "reagents": {
                    "qpcr_master_mix": {"total_volume_required": 280},
                    "template_dna": {"minimum_volume_needed": 130}
                  }
                }
                """,
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["reagent_totals_match_task_spec"])

    def test_dynamic_task_defers_static_reagent_total_check(self) -> None:
        task = AuthoringTask(
            task_id="T909",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt="Read a CSV sample sheet uploaded as a runtime CSV parameter.",
            spec=TaskSpec(
                default_samples=24,
                reagents=(TaskReagentSpec(name="diluent", volume_per_sample_uL=30),),
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "reagent_plan.json").write_text(
                '{"reagents": [{"name": "Diluent", "notes": "N x 30 uL"}]}',
                encoding="utf-8",
            )

            result = validate_semantics(package_dir, task)

        self.assertTrue(result.checks["reagent_totals_static_check_deferred"])
        self.assertNotIn("reagent_total_mismatch", [issue.code for issue in result.issues])

    def test_non_dynamic_task_param_sweep_passes(self) -> None:
        task = AuthoringTask(
            task_id="T910",
            source="test",
            difficulty="Easy",
            holdout=False,
            output_contract="execution_package",
            prompt="Transfer 25 uL buffer into 8 wells.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)

            result = validate_param_sweep(package_dir, task)

        self.assertTrue(result.ok)
        self.assertFalse(result.dynamic_task)

    def test_dynamic_task_param_sweep_accepts_parameterized_package(self) -> None:
        task = AuthoringTask(
            task_id="T911",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt=(
                "Expose a runtime parameter sample_count that only accepts 8, 16, or 24. "
                "Recompute reagent_plan.json totals and tip_plan.json counts from sample_count."
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "protocol.py").write_text(
                """
def add_parameters(parameters):
    parameters.add_int("sample_count", display_name="Sample Count", default=8)

def run(protocol):
    sample_count = protocol.params.sample_count
""",
                encoding="utf-8",
            )
            (package_dir / "tip_plan.json").write_text(
                '{"tips_required": "computed from runtime parameter sample_count"}',
                encoding="utf-8",
            )
            (package_dir / "reagent_plan.json").write_text(
                '{"reagents": [{"name": "buffer", "total": "sample_count * 25 uL"}]}',
                encoding="utf-8",
            )

            result = validate_param_sweep(package_dir, task)

        self.assertTrue(result.ok)
        self.assertTrue(result.dynamic_task)

    def test_dynamic_task_param_sweep_flags_hard_coded_default(self) -> None:
        task = AuthoringTask(
            task_id="T912",
            source="test",
            difficulty="Hard",
            holdout=False,
            output_contract="execution_package",
            prompt=(
                "Expose a runtime parameter replicate_count in {1, 2, 3, 4}. "
                "Update reagent_plan.json totals and tip_plan.json counts to match replicate_count automatically."
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            write_valid_package(package_dir)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n    destinations = 24\n",
                encoding="utf-8",
            )
            (package_dir / "tip_plan.json").write_text(
                '{"tips_required": 24}',
                encoding="utf-8",
            )

            result = validate_param_sweep(package_dir, task)

        self.assertFalse(result.ok)
        self.assertIn("replicate_count_protocol_not_parameterized", [issue.code for issue in result.issues])
        self.assertIn("replicate_count_plan_not_parameterized", [issue.code for issue in result.issues])


if __name__ == "__main__":
    unittest.main()
