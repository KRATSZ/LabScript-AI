from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
from unittest import mock

from labscriptai.benchmark.authoring_pilot import (
    _add_deterministic_protocol_guards,
    _offline_author,
    _selected_tasks,
    repair_package_metadata,
    run_authoring_pilot,
    stamp_manifest,
)
from labscriptai.benchmark.tasks import AuthoringTask


ROOT = Path(__file__).resolve().parents[1]


class AuthoringPilotTests(unittest.TestCase):
    def test_selected_tasks_can_reach_30_task_holdout(self) -> None:
        manifest = json.loads((ROOT / "benchmarks" / "authoring" / "holdout_manifest.json").read_text())
        holdout_ids = set(manifest["holdout_task_ids"])
        selected = _selected_tasks(ROOT / "benchmarks" / "authoring" / "tasks.yaml", limit=30)

        self.assertEqual(len(selected), 30)
        self.assertTrue(all(task.holdout for task in selected))
        self.assertEqual({task.task_id for task in selected}, holdout_ids)

    def test_selected_tasks_accepts_exact_task_ids(self) -> None:
        selected = _selected_tasks(
            ROOT / "benchmarks" / "authoring" / "tasks.yaml",
            limit=1,
            task_ids=("T088", "T056"),
        )

        self.assertEqual([task.task_id for task in selected], ["T088", "T056"])

    def test_offline_authoring_pilot_writes_valid_placeholder_packages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            summary = run_authoring_pilot(
                tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                output_dir=output_dir,
                package_author=lambda task: _offline_author(task, model_id="offline-test"),
                model_id="offline-test",
                limit=3,
            )

        self.assertEqual(summary["task_count"], 3)
        self.assertEqual(summary["package_complete_count"], 3)
        self.assertEqual(summary["deterministic_pass_count"], 3)
        self.assertEqual(summary["validator_ok_count"], 0)

    def test_stamp_manifest_fills_harness_owned_fields(self) -> None:
        task = AuthoringTask(
            task_id="T999",
            source="test",
            difficulty="Easy",
            holdout=False,
            output_contract="execution_package",
            prompt="Do the thing.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "manifest.json").write_text("{}", encoding="utf-8")

            stamp_manifest(package_dir, task, model_id="model-x")

            manifest = (package_dir / "manifest.json").read_text(encoding="utf-8")

        self.assertIn('"tool_permissions"', manifest)
        self.assertIn('"model_id": "model-x"', manifest)

    def test_authoring_pilot_can_include_simulation_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            with mock.patch(
                "labscriptai.benchmark.authoring_pilot.simulate_protocol_file",
                return_value={"ok": True, "returncode": 0},
            ):
                summary = run_authoring_pilot(
                    tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                    output_dir=output_dir,
                    package_author=lambda task: _offline_author(task, model_id="offline-test"),
                    model_id="offline-test",
                    limit=1,
                    simulate=True,
                )

        self.assertEqual(summary["simulation_attempted_count"], 1)
        self.assertEqual(summary["simulation_pass_count"], 1)
        self.assertEqual(summary["first_pass_simulation_pass_count"], 1)
        self.assertEqual(summary["attempts_per_task"], {"T056": 1})
        self.assertEqual(summary["simulator_calls"], 1)
        self.assertEqual(summary["validator_ok_count"], 1)
        self.assertEqual(summary["first_pass_validator_pass_count"], 1)
        self.assertEqual(summary["repaired_simulation_pass_count"], 0)
        self.assertEqual(summary["provider_error_count"], 0)

    def test_authoring_pilot_persists_trace_artifact(self) -> None:
        def author(task):
            files = _offline_author(task, model_id="offline-test")
            files["trace.jsonl"] = '{"event_type":"tool_call","payload":{"name":"write_file"}}\n'
            return files

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            run_authoring_pilot(
                tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                output_dir=output_dir,
                package_author=author,
                model_id="offline-test",
                limit=1,
            )

            trace = output_dir / "T056" / "attempt1" / "package" / "trace.jsonl"
            trace_exists = trace.exists()

        self.assertTrue(trace_exists)

    def test_simulation_failure_repairs_only_protocol_py_on_next_attempt(self) -> None:
        simulations = [
            {"ok": False, "returncode": 1, "stdout": "", "stderr": "bad protocol"},
            {"ok": True, "returncode": 0, "stdout": "ok", "stderr": ""},
        ]

        def repairer(task, protocol_py, simulation_result):
            del task
            self.assertIn("placeholder", protocol_py)
            self.assertEqual(simulation_result["stderr"], "bad protocol")
            return protocol_py.replace("placeholder", "repaired")

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            with mock.patch(
                "labscriptai.benchmark.authoring_pilot.simulate_protocol_file",
                side_effect=simulations,
            ):
                summary = run_authoring_pilot(
                    tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                    output_dir=output_dir,
                    package_author=lambda task: _offline_author(task, model_id="offline-test"),
                    model_id="offline-test",
                    limit=1,
                    simulate=True,
                    protocol_repairer=repairer,
                    simulation_repair_attempts=3,
                )
            attempt1 = output_dir / "T056" / "attempt1" / "package"
            attempt2 = output_dir / "T056" / "attempt2" / "package"
            protocol1 = (attempt1 / "protocol.py").read_text(encoding="utf-8")
            protocol2 = (attempt2 / "protocol.py").read_text(encoding="utf-8")
            manifest1 = json.loads((attempt1 / "manifest.json").read_text(encoding="utf-8"))
            manifest2 = json.loads((attempt2 / "manifest.json").read_text(encoding="utf-8"))

        self.assertIn("placeholder", protocol1)
        self.assertIn("repaired", protocol2)
        self.assertEqual(manifest1["deck"], manifest2["deck"])
        self.assertEqual(summary["first_pass_simulation_pass_count"], 0)
        self.assertEqual(summary["simulation_pass_count"], 1)
        self.assertEqual(summary["simulation_repair_attempts"], 1)
        self.assertEqual(summary["repair_success_count"], 1)
        self.assertEqual(summary["repaired_simulation_pass_count"], 1)
        self.assertEqual(summary["repaired_validator_pass_count"], 1)
        self.assertEqual(summary["avg_repair_attempts_when_repaired"], 1)
        self.assertEqual(summary["max_repair_attempts_observed"], 1)
        self.assertEqual(summary["attempts_per_task"], {"T056": 2})
        self.assertTrue(summary["records"][0]["simulator_summary"]["ok"])

    def test_simulation_repair_retries_after_transient_repairer_error(self) -> None:
        simulations = [
            {"ok": False, "returncode": 1, "stdout": "", "stderr": "bad protocol"},
            {"ok": True, "returncode": 0, "stdout": "ok", "stderr": ""},
        ]
        calls = {"count": 0}

        def repairer(task, protocol_py, simulation_result):
            del task, protocol_py, simulation_result
            calls["count"] += 1
            if calls["count"] == 1:
                raise ConnectionError("repair provider disconnected")
            return 'metadata = {"protocolName": "repaired", "apiLevel": "2.15"}\ndef run(protocol):\n    pass\n'

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            with mock.patch(
                "labscriptai.benchmark.authoring_pilot.simulate_protocol_file",
                side_effect=simulations,
            ):
                summary = run_authoring_pilot(
                    tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                    output_dir=output_dir,
                    package_author=lambda task: _offline_author(task, model_id="offline-test"),
                    model_id="offline-test",
                    limit=1,
                    simulate=True,
                    protocol_repairer=repairer,
                    simulation_repair_attempts=2,
                )

        record = summary["records"][0]
        self.assertEqual(summary["simulation_pass_count"], 1)
        self.assertEqual(summary["simulation_repair_attempts"], 2)
        self.assertEqual(summary["repair_success_count"], 1)
        self.assertEqual(record["repair_errors"], ["ConnectionError: repair provider disconnected"])
        self.assertEqual(summary["attempts_per_task"], {"T056": 3})

    def test_authoring_pilot_retries_and_writes_record(self) -> None:
        calls = {"count": 0}

        def flaky_author(task):
            calls["count"] += 1
            if calls["count"] == 1:
                raise ValueError("truncated json")
            return _offline_author(task, model_id="offline-test")

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            summary = run_authoring_pilot(
                tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                output_dir=output_dir,
                package_author=flaky_author,
                model_id="offline-test",
                limit=1,
                retry_attempts=2,
            )
            record = json.loads((output_dir / "T056" / "record.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["total_attempts"], 2)
        self.assertEqual(summary["provider_error_count"], 1)
        self.assertEqual(summary["provider_errors_per_task"], {"T056": 1})
        self.assertEqual(summary["generation_attempts_per_task"], {"T056": 2})
        self.assertEqual(record["attempts"], 2)
        self.assertEqual(record["provider_error_count"], 1)
        self.assertEqual(record["prior_errors"], ["ValueError: truncated json"])

    def test_authoring_pilot_can_recover_after_multiple_generation_transients(self) -> None:
        calls = {"count": 0}

        def flaky_author(task):
            calls["count"] += 1
            if calls["count"] < 4:
                raise ConnectionError("provider disconnected")
            return _offline_author(task, model_id="offline-test")

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "authoring"
            summary = run_authoring_pilot(
                tasks_path=ROOT / "benchmarks" / "authoring" / "tasks.yaml",
                output_dir=output_dir,
                package_author=flaky_author,
                model_id="offline-test",
                limit=1,
                retry_attempts=4,
            )
            record = json.loads((output_dir / "T056" / "record.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["total_attempts"], 4)
        self.assertEqual(record["generation_attempts"], 4)
        self.assertEqual(
            record["prior_errors"],
            [
                "ConnectionError: provider disconnected",
                "ConnectionError: provider disconnected",
                "ConnectionError: provider disconnected",
            ],
        )

    def test_repair_package_metadata_adds_instruments_and_risk_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    protocol.load_instrument('p300_single_gen2', 'left')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text('{"labware": []}', encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text(
                '[{"risk": "cross contamination"}]',
                encoding="utf-8",
            )

            repairs = repair_package_metadata(package_dir)

            deck_plan = (package_dir / "deck_plan.json").read_text(encoding="utf-8")
            risk_checklist = (package_dir / "risk_checklist.json").read_text(encoding="utf-8")

        self.assertTrue(any("instrument" in repair for repair in repairs))
        self.assertIn('"p300_single_gen2"', deck_plan)
        self.assertIn('"critical_failures"', risk_checklist)

    def test_repair_package_metadata_adds_protocol_labware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    protocol.load_labware('corning_96_wellplate_360ul_flat', 'B1')\n"
                "    protocol.load_labware(load_name='opentrons_flex_96_tiprack_200ul', location='D1')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text('{"labware": []}', encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            deck_plan = json.loads((package_dir / "deck_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("labware" in repair for repair in repairs))
        self.assertIn(
            {"name": "corning_96_wellplate_360ul_flat", "load_name": "corning_96_wellplate_360ul_flat", "slot": "B1"},
            deck_plan["labware"],
        )
        self.assertIn(
            {"name": "opentrons_flex_96_tiprack_200ul", "load_name": "opentrons_flex_96_tiprack_200ul", "slot": "D1"},
            deck_plan["labware"],
        )

    def test_repair_package_metadata_adds_flex_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "from opentrons import protocol_api\n\n"
                "metadata = {\"apiLevel\": \"2.15\"}\n\n"
                "def run(protocol: protocol_api.ProtocolContext):\n"
                "    protocol.load_instrument('flex_1channel_1000', 'left')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("Flex protocol requirements" in repair for repair in repairs))
        self.assertIn('requirements = {"robotType": "Flex", "apiLevel": "2.24"}', protocol_py)

    def test_repair_package_metadata_normalizes_flex_alias_and_stale_deck_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    protocol.load_instrument('flex_1channel_200ul', mount='left')\n"
                "    protocol.load_labware('opentrons_flex_96_tiprack_200ul', 'A1')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text(
                json.dumps(
                    {
                        "pipettes": [{"name": "p300_single_gen3", "mount": "left"}],
                        "labware": [
                            {"name": "opentrons_flex_96_tiprack_300ul", "slot": "A1"},
                            {"name": "p300_single_gen3", "load_name": "p300_single_gen3", "slot": "left"},
                        ],
                        "instruments": [{"name": "p300_single_gen3", "type": "p300_single_gen3", "mount": "left"}],
                    }
                ),
                encoding="utf-8",
            )
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")
            deck_plan = json.loads((package_dir / "deck_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("normalized flex_1channel_200ul" in repair for repair in repairs))
        self.assertIn("flex_1channel_1000", protocol_py)
        self.assertNotIn("flex_1channel_200ul", protocol_py)
        self.assertEqual(
            deck_plan["labware"],
            [
                {
                    "name": "opentrons_flex_96_tiprack_200ul",
                    "load_name": "opentrons_flex_96_tiprack_200ul",
                    "slot": "A1",
                }
            ],
        )
        self.assertEqual(deck_plan["instruments"], [{"name": "flex_1channel_1000", "type": "flex_1channel_1000", "mount": "left"}])
        self.assertEqual(deck_plan["pipettes"], [{"name": "flex_1channel_1000", "mount": "left"}])

    def test_repair_package_metadata_normalizes_gen3_flex_hallucinations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n'
                "def run(protocol):\n"
                "    protocol.load_instrument('p300_single_gen3', mount='left')\n"
                "    protocol.load_labware('opentrons_flex_96_tiprack_300ul', location='A1')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")
            deck_plan = json.loads((package_dir / "deck_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("p300_single_gen3" in repair for repair in repairs))
        self.assertTrue(any("opentrons_flex_96_tiprack_300ul" in repair for repair in repairs))
        self.assertIn("flex_1channel_1000", protocol_py)
        self.assertIn("opentrons_flex_96_tiprack_200ul", protocol_py)
        self.assertEqual(deck_plan["instruments"], [{"name": "flex_1channel_1000", "type": "flex_1channel_1000", "mount": "left"}])
        self.assertEqual(
            deck_plan["labware"],
            [
                {
                    "name": "opentrons_flex_96_tiprack_200ul",
                    "load_name": "opentrons_flex_96_tiprack_200ul",
                    "slot": "A1",
                }
            ],
        )

    def test_repair_package_metadata_normalizes_gen2_pipette_in_flex_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n'
                "def run(protocol):\n"
                "    protocol.load_instrument('p300_single_gen2', mount='left')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text(
                json.dumps({"instruments": [{"name": "p300_single_gen2", "type": "p300_single_gen2", "mount": "left"}]}),
                encoding="utf-8",
            )
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")
            deck_plan = json.loads((package_dir / "deck_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("p300_single_gen2" in repair for repair in repairs))
        self.assertIn("flex_1channel_1000", protocol_py)
        self.assertEqual(deck_plan["instruments"], [{"name": "flex_1channel_1000", "type": "flex_1channel_1000", "mount": "left"}])

    def test_repair_package_metadata_normalizes_flex_wellplate_hallucination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n'
                "def run(protocol):\n"
                "    protocol.load_labware('opentrons_flex_96_wellplate_200ul', location='D1')\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")
            deck_plan = json.loads((package_dir / "deck_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("opentrons_flex_96_wellplate_200ul" in repair for repair in repairs))
        self.assertIn("opentrons_96_wellplate_200ul_pcr_full_skirt", protocol_py)
        self.assertEqual(
            deck_plan["labware"],
            [
                {
                    "name": "opentrons_96_wellplate_200ul_pcr_full_skirt",
                    "load_name": "opentrons_96_wellplate_200ul_pcr_full_skirt",
                    "slot": "D1",
                }
            ],
        )

    def test_repair_package_metadata_binds_unassigned_tiprack_and_flex_trash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n'
                "def run(protocol):\n"
                "    pipette = protocol.load_instrument('flex_1channel_1000', mount='left')\n"
                "    tiprack = protocol.load_labware('opentrons_flex_96_tiprack_200ul', location='C1')\n"
                "    plate = protocol.load_labware('nest_96_wellplate_200ul_flat', location='D1')\n"
                "    pipette.pick_up_tip()\n"
                "    pipette.aspirate(20, plate['A1'])\n"
                "    pipette.dispense(20, plate['A2'])\n"
                "    pipette.drop_tip()\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("bound pipette to tiprack" in repair for repair in repairs))
        self.assertTrue(any("Flex trash bin" in repair for repair in repairs))
        self.assertIn("pipette.tip_racks = [tiprack]", protocol_py)
        self.assertIn('protocol.load_trash_bin("A3")', protocol_py)

    def test_repair_package_metadata_normalizes_pipette_loaded_as_labware(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "Flex", "apiLevel": "2.24"}\n\n'
                "def run(protocol):\n"
                "    pipette = protocol.load_labware(\n"
                "        \"flex_1channel_1000\", mount=\"left\"\n"
                "    )\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("pipette load_labware" in repair for repair in repairs))
        self.assertIn("protocol.load_instrument('flex_1channel_1000', mount='left')", protocol_py)
        self.assertNotIn("protocol.load_labware", protocol_py)

    def test_repair_package_metadata_does_not_bind_before_loaded_instrument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                'requirements = {"robotType": "OT-2", "apiLevel": "2.15"}\n\n'
                "def run(protocol):\n"
                "    tip_rack = protocol.load_labware('opentrons_96_tiprack_300ul', location='3')\n"
                "    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', location='1')\n"
                "    p300 = protocol.load_instrument('p300_single_gen2', mount='right', tip_racks=[tip_rack])\n"
                "    p300.pick_up_tip()\n"
                "    p300.aspirate(20, plate['A1'])\n"
                "    p300.dispense(20, plate['A2'])\n"
                "    p300.drop_tip()\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertFalse(any("bound p300" in repair for repair in repairs))
        self.assertNotIn("p300.tip_racks = [tip_rack]", protocol_py)

    def test_repair_package_metadata_moves_data_paths_to_tmp_for_simulator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "SAMPLE_SHEET_PATH = '/data/sample_sheet.csv'\n"
                'MANIFEST_OUT_PATH = "/data/manifest_output.json"\n\n'
                "def run(protocol):\n"
                "    protocol.comment(SAMPLE_SHEET_PATH)\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("/data file path" in repair for repair in repairs))
        self.assertIn("'/tmp/sample_sheet.csv'", protocol_py)
        self.assertIn('"/tmp/manifest_output.json"', protocol_py)
        self.assertNotIn("/data/", protocol_py)

    def test_repair_package_metadata_flattens_columns_by_name_iteration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    source_plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)\n"
                "    all_sample_wells = [\n"
                "        well\n"
                "        for col in source_plate.columns_by_name()[\"1\"]\n"
                "        + source_plate.columns_by_name()[\"2\"]\n"
                "        + source_plate.columns_by_name()[\"3\"]\n"
                "        for well in col\n"
                "    ]\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("columns_by_name well iteration" in repair for repair in repairs))
        self.assertIn('for well in source_plate.columns_by_name()["1"]', protocol_py)
        self.assertNotIn("for col in source_plate.columns_by_name()", protocol_py)
        self.assertNotIn("for well in col", protocol_py)

    def test_repair_package_metadata_normalizes_p300_minimum_volume_constant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "metadata = {'apiLevel': '2.18'}\n\n"
                "def add_parameters(parameters):\n"
                "    parameters.add_str(variable_name='pipette_type', default='p300_single_gen2')\n\n"
                "REQUIRED_MIN_VOL = 2.0\n"
                "REQUIRED_MAX_VOL = 200.0\n\n"
                "def run(protocol):\n"
                "    pass\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_py = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertTrue(any("p300 minimum required volume" in repair for repair in repairs))
        self.assertIn("REQUIRED_MIN_VOL = 20.0", protocol_py)

    def test_repair_package_metadata_adds_tip_quantities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    pipette.pick_up_tip()\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text('{"tip_racks": []}', encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            tip_plan = json.loads((package_dir / "tip_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("tip_plan quantities" in repair for repair in repairs))
        self.assertEqual(tip_plan["tips_required"], 1)
        self.assertEqual(tip_plan["tips_available"], 96)

    def test_repair_package_metadata_normalizes_tip_quantity_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                "def run(protocol):\n"
                "    pipette.pick_up_tip()\n",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text(
                json.dumps(
                    {
                        "tip_racks": [
                            {"slot": "4", "labware": "opentrons_96_tiprack_300ul", "capacity": 96},
                            {"slot": "6", "labware": "opentrons_96_tiprack_300ul", "capacity": 96},
                            {"slot": "7", "labware": "opentrons_96_tiprack_300ul", "capacity": 96},
                        ],
                        "total_tips_available": 288,
                        "tips_required": {
                            "master_mix_phase": 1,
                            "template_phase": 96,
                            "total": 97,
                        },
                        "tips_available": 96,
                    }
                ),
                encoding="utf-8",
            )

            repairs = repair_package_metadata(package_dir)
            tip_plan = json.loads((package_dir / "tip_plan.json").read_text(encoding="utf-8"))

        self.assertTrue(any("tip_plan quantities" in repair for repair in repairs))
        self.assertEqual(tip_plan["tips_required"], 97)
        self.assertEqual(tip_plan["tips_available"], 288)

    def test_repair_package_metadata_removes_duplicate_fixed_trash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                """
from opentrons import protocol_api

metadata = {"apiLevel": "2.15"}

def run(protocol: protocol_api.ProtocolContext):
    trash = protocol.load_labware("opentrons_1_trash_1100ml_fixed", "12")
    tiprack = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tiprack])
    pipette.pick_up_tip()
    pipette.aspirate(10, plate["A1"])
    pipette.dispense(10, plate["A2"])
    pipette.drop_tip()
""",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_text = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertIn("removed duplicate fixed trash labware load", repairs)
        self.assertNotIn("opentrons_1_trash_1100ml_fixed", protocol_text)

    def test_repair_package_metadata_splits_current_volume_dispense(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                """
from opentrons import protocol_api

metadata = {"apiLevel": "2.15"}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    plate = protocol.load_labware("nest_96_wellplate_2ml_deep", "2")
    trash = protocol.fixed_trash
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tiprack])
    p300.pick_up_tip()
    total_vol = 920
    p300.aspirate(total_vol, plate["A1"].bottom(1))
    p300.dispense(p300.current_volume, trash["A1"])
    p300.drop_tip()
""",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_text = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertIn("split oversized aspirate/dispense pairs", repairs)
        self.assertIn("def _safe_aspirate_dispense", protocol_text)
        self.assertIn("_safe_aspirate_dispense(p300, total_vol", protocol_text)

    def test_deterministic_protocol_guards_do_not_make_safe_helpers_recursive(self) -> None:
        protocol_text = '''from opentrons import protocol_api

def _safe_aspirate_dispense(pipette, volume, source, destination):
    remaining = float(volume)
    max_volume = float(getattr(pipette, "max_volume", 300))
    while remaining > 0:
        step = min(remaining, max_volume)
        _safe_aspirate_dispense(pipette, step, source, destination)
        remaining -= step

def _safe_mix(pipette, repetitions, volume, location):
    step = min(float(volume), float(getattr(pipette, "max_volume", 300)))
    _safe_mix(pipette, repetitions, step, location)

def run(protocol):
    temp_mod = protocol.load_module("temperature module gen2", 1)
    temp_mod.set_temperature(4)
    temp_mod.wait_for_temp()
'''

        repaired, repairs = _add_deterministic_protocol_guards(protocol_text)

        self.assertIn("removed unsupported temperature wait call", repairs)
        self.assertIn("canonicalized deterministic safe helper bodies", repairs)
        self.assertIn("pipette.aspirate(step, source)", repaired)
        self.assertIn("pipette.dispense(step, destination)", repaired)
        self.assertIn("pipette.mix(int(repetitions), step, location)", repaired)
        self.assertNotIn("wait_for_temp()", repaired)
        helper_body = repaired.split("def run(protocol):", 1)[0]
        self.assertNotIn("    _safe_aspirate_dispense(pipette, step", helper_body)
        self.assertNotIn("    _safe_mix(pipette, repetitions", helper_body)

    def test_repair_package_metadata_opens_thermocycler_lid_before_pipetting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                """
from opentrons import protocol_api

metadata = {"apiLevel": "2.15"}

def run(protocol: protocol_api.ProtocolContext):
    tiprack = protocol.load_labware("opentrons_96_tiprack_20ul", "1")
    tube_rack = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", "2")
    tc_mod = protocol.load_module("thermocycler module", "7")
    tc_plate = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    p20 = protocol.load_instrument("p20_single_gen2", "left", tip_racks=[tiprack])
    p20.pick_up_tip()
    p20.aspirate(10, tube_rack["A1"])
    p20.dispense(10, tc_plate["A1"])
    p20.drop_tip()
""",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_text = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertIn("opened thermocycler lid before pipetting to module labware", repairs)
        self.assertIn("tc_mod.open_lid()", protocol_text)

    def test_repair_package_metadata_makes_reagent_lookup_alias_tolerant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text(
                """
from opentrons import protocol_api

metadata = {"apiLevel": "2.15"}

def run(ctx: protocol_api.ProtocolContext):
    reagent_plan = {"reagents": {"buffer": {"source_slot": "3", "source_well": "A1"}}}
    for reagent_id, rcfg in reagent_plan.get("reagents", {}).items():
        slot = rcfg["slot"]
        well = rcfg["well"]
""",
                encoding="utf-8",
            )
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text("{}", encoding="utf-8")
            (package_dir / "tip_plan.json").write_text("{}", encoding="utf-8")

            repairs = repair_package_metadata(package_dir)
            protocol_text = (package_dir / "protocol.py").read_text(encoding="utf-8")

        self.assertIn("made reagent slot lookup tolerant of plan aliases", repairs)
        self.assertIn('rcfg.get("source_slot")', protocol_text)
        self.assertIn('rcfg.get("source_well")', protocol_text)

    def test_repair_package_metadata_moves_structured_critical_failures_to_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text("def run(protocol):\n    pass\n", encoding="utf-8")
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text(
                '{"critical_failures": [{"condition": "bad csv"}]}',
                encoding="utf-8",
            )

            repairs = repair_package_metadata(package_dir)
            risk_checklist = (package_dir / "risk_checklist.json").read_text(encoding="utf-8")

        self.assertTrue(any("structured critical_failures" in repair for repair in repairs))
        self.assertIn('"risks"', risk_checklist)

    def test_repair_package_metadata_moves_unknown_critical_failures_to_risks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text("def run(protocol):\n    pass\n", encoding="utf-8")
            (package_dir / "deck_plan.json").write_text("{}", encoding="utf-8")
            (package_dir / "risk_checklist.json").write_text(
                json.dumps(
                    {
                        "critical_failures": [
                            "collision",
                            "Confirm source concentration before starting",
                            42,
                        ],
                        "risks": ["existing risk"],
                    }
                ),
                encoding="utf-8",
            )

            repairs = repair_package_metadata(package_dir)
            risk_checklist = json.loads((package_dir / "risk_checklist.json").read_text(encoding="utf-8"))

        self.assertTrue(any("unknown critical_failures" in repair for repair in repairs))
        self.assertEqual(risk_checklist["critical_failures"], ["collision"])
        self.assertEqual(
            risk_checklist["risks"],
            ["existing risk", "Confirm source concentration before starting", 42],
        )

    def test_repair_three_piece_manifest_moves_non_enum_critical_failures_to_risk_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "protocol.py").write_text("def run(protocol):\n    pass\n", encoding="utf-8")
            (package_dir / "setup_card.html").write_text("<h1>Setup</h1>\n", encoding="utf-8")
            (package_dir / "manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "0.4",
                        "deck": {"slots": [], "modules": [], "instruments": []},
                        "reagents": [],
                        "tips": {"tips_required": 1, "tips_available": 96},
                        "risk_flags": ["existing risk"],
                        "critical_failures": [
                            "collision",
                            {"condition": "Tip rack exhausted"},
                            "tip_not_changed_between_columns",
                        ],
                        "off_platform_handoff": {"declared": False},
                        "tool_permissions": ["simulate_protocol"],
                        "budget": {"attempts": 8, "wall_min": 30, "tokens": 24000},
                    }
                ),
                encoding="utf-8",
            )

            repairs = repair_package_metadata(package_dir)
            manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))

        self.assertTrue(any("non-enum manifest critical_failures" in repair for repair in repairs))
        self.assertEqual(manifest["critical_failures"], ["collision"])
        self.assertEqual(
            manifest["risk_flags"],
            ["existing risk", {"condition": "Tip rack exhausted"}, "tip_not_changed_between_columns"],
        )


if __name__ == "__main__":
    unittest.main()
