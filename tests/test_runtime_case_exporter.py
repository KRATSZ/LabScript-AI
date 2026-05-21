from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.adapters.robot_http import RobotHttpConfig, RobotHttpReadOnlyAdapter
from labscriptai.runtime.cases import case_from_snapshot, classify_error, collect_runtime_cases, load_cases


class FakeCaseRobotAdapter(RobotHttpReadOnlyAdapter):
    def __init__(self) -> None:
        super().__init__(RobotHttpConfig(host="robot.local"))

    def _get(self, path, query=None):  # noqa: ANN001
        del query
        payloads = {
            "/health": {
                "data": {
                    "robot_serial": "FLX-CASE",
                    "robot_model": "OT-3 Standard",
                }
            },
            "/modules": {"data": [{"model": "thermocyclerModuleV2", "serialNumber": "TC-1"}]},
            "/runs": {
                "data": [
                    {"id": "run-ok", "status": "succeeded"},
                    {"id": "run-failed", "status": "failed"},
                ]
            },
            "/runs/run-failed": {
                "data": {
                    "id": "run-failed",
                    "status": "failed",
                    "createdAt": "2026-05-20T00:00:00Z",
                    "errors": [
                        {
                            "detail": "ERR408:thermal:Thermal drift of more than 4C",
                        }
                    ],
                }
            },
            "/runs/run-failed/commands": {
                "data": [
                    {"id": "cmd-1", "commandType": "home", "status": "succeeded"},
                    {"id": "cmd-2", "commandType": "thermocycler/closeLid", "status": "failed"},
                ]
            },
        }
        return payloads[path]


class RuntimeCaseExporterTests(unittest.TestCase):
    def test_classifies_thermocycler_drift(self) -> None:
        category = classify_error("ERR408:thermal:Thermal drift of more than 4C")

        self.assertEqual(category, "thermocycler_thermal_drift")

    def test_case_from_snapshot_sets_manual_module_policy(self) -> None:
        adapter = FakeCaseRobotAdapter()
        snapshot = adapter.snapshot(run_id="run-failed")

        case = case_from_snapshot(snapshot, source="test")

        self.assertEqual(case.error_category, "thermocycler_thermal_drift")
        self.assertEqual(case.expected_policy, "human_module_check_required")
        self.assertIn("request_human_confirmation", case.allowed_action_types)
        self.assertEqual(case.state.phase, "recovering")
        self.assertEqual(case.state.robot["id"], "FLX-CASE")

    def test_collect_runtime_cases_writes_index_and_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            summary = collect_runtime_cases(
                FakeCaseRobotAdapter(),
                output_dir=output_dir,
                limit=5,
            )
            cases = load_cases(output_dir)

            trace_exists = (output_dir / "case-run-failed" / "trace.jsonl").exists()
            index_exists = (output_dir / "index.jsonl").exists()

        self.assertEqual(summary["case_count"], 1)
        self.assertEqual(cases[0].case_id, "case-run-failed")
        self.assertTrue(trace_exists)
        self.assertTrue(index_exists)


if __name__ == "__main__":
    unittest.main()
