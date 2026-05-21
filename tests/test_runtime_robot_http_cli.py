from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from labscriptai.runtime.adapters.robot_http import RobotHttpConfig, RobotHttpReadOnlyAdapter
from labscriptai.runtime.cli import main as runtime_cli_main
from test_package_validator import write_valid_package


class FakeRobotAdapter(RobotHttpReadOnlyAdapter):
    def __init__(self) -> None:
        super().__init__(RobotHttpConfig(host="robot.local"))

    def _get(self, path, query=None):  # noqa: ANN001
        del query
        payloads = {
            "/health": {"data": {"robot_serial": "FLX-1", "robot_model": "Flex"}},
            "/modules": {"data": []},
            "/runs": {"data": [{"id": "run-1"}]},
            "/runs/run-1": {"data": {"id": "run-1", "status": "awaiting-recovery"}},
            "/runs/run-1/commands": {
                "data": [
                    {"id": "cmd-1", "commandType": "pickUpTip", "status": "succeeded"},
                    {"id": "cmd-2", "commandType": "aspirate", "status": "failed"},
                ]
            },
        }
        return payloads[path]


class RuntimeRobotHttpCliTests(unittest.TestCase):
    def test_robot_http_snapshot_builds_state_ledger(self) -> None:
        adapter = FakeRobotAdapter()

        snapshot = adapter.snapshot(run_id="run-1")
        state = adapter.state_from_snapshot(run_id="run-1", snapshot=snapshot)

        self.assertEqual(state.robot["id"], "FLX-1")
        self.assertEqual(state.phase, "recovering")
        self.assertEqual(state.completed_commands[0]["id"], "cmd-1")
        self.assertEqual(state.failed_commands[0]["id"], "cmd-2")

    def test_cli_chat_dry_run_writes_trace_and_patch_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            patch = {
                "schema_version": "0.1",
                "patch_id": "patch-cli",
                "recovery_type": "continuation_protocol",
                "human_confirmed": True,
                "operations": [
                    {
                        "op_type": "transfer",
                        "tip": "A1",
                        "source_well": "reservoir:A1",
                        "destination_well": "plate:A1",
                        "reagent": "water",
                        "volume_ul": 5,
                    }
                ],
            }
            candidate = {
                "action_type": "validate_continuation_patch",
                "reason": "Validate CLI patch.",
                "parameters": {"patch": patch},
            }
            trace_path = root / "trace.jsonl"
            patch_log_path = root / "patch_log.jsonl"

            exit_code = runtime_cli_main(
                [
                    "chat",
                    "--dry-run",
                    "--run-id",
                    "run-1",
                    "--package-dir",
                    str(package_dir),
                    "--trace-path",
                    str(trace_path),
                    "--patch-log-path",
                    str(patch_log_path),
                    "--simulation-pass",
                    "--candidate-json",
                    json.dumps(candidate),
                ]
            )
            trace_exists = trace_path.exists()
            patch_log_exists = patch_log_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(trace_exists)
        self.assertTrue(patch_log_exists)

    def test_cli_chat_defaults_to_tui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)

            with patch("labscriptai.runtime.tui.RuntimeTuiApp.run", return_value=0) as run:
                exit_code = runtime_cli_main(
                    [
                        "chat",
                        "--dry-run",
                        "--run-id",
                        "run-1",
                        "--package-dir",
                        str(package_dir),
                        "--provider",
                        "offline",
                    ]
                )

        self.assertEqual(exit_code, 0)
        run.assert_called_once()

    def test_cli_chat_dry_run_opens_tui_without_deepseek_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)

            with patch.dict("os.environ", {}, clear=True):
                with patch("labscriptai.runtime.tui.RuntimeTuiApp.run", return_value=0) as run:
                    exit_code = runtime_cli_main(
                        [
                            "chat",
                            "--dry-run",
                            "--run-id",
                            "run-1",
                            "--package-dir",
                            str(package_dir),
                            "--provider",
                            "deepseek",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        run.assert_called_once()

    def test_cli_chat_no_tui_requires_candidate_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)

            exit_code = runtime_cli_main(
                [
                    "chat",
                    "--dry-run",
                    "--run-id",
                    "run-1",
                    "--package-dir",
                    str(package_dir),
                    "--provider",
                    "offline",
                    "--no-tui",
                ]
            )

        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
