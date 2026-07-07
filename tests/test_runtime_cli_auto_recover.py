from __future__ import annotations

import json
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from labscriptai.runtime.cli import main as runtime_cli_main


def _decode_json_stream(text: str) -> list[dict]:
    decoder = json.JSONDecoder()
    index = 0
    objects: list[dict] = []
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        loaded, index = decoder.raw_decode(text, index)
        objects.append(loaded)
    return objects


class RuntimeCliAutoRecoverTests(unittest.TestCase):
    def test_auto_recover_shadow_mode_stops_after_awaiting_confirmation(self) -> None:
        summaries = [
            {"status": "awaiting_confirmation", "preview": {"branch": "retry_pick_up_tip_with_next_candidate"}},
        ]

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                return summaries.pop(0)

        buffer = StringIO()
        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load") as load_queue:
                with patch("labscriptai.runtime.cli._mcp_adapter") as mcp_adapter:
                    adapter = mcp_adapter.return_value
                    adapter.recovery_snapshot.return_value = {"parse_error": {"data": {}}}
                    adapter.state_from_snapshot.return_value = object()
                    load_queue.return_value = object()
                    with patch("sys.stdout", buffer):
                        exit_code = runtime_cli_main(
                            [
                                "auto-recover",
                                "--robot-ip",
                                "10.0.0.2",
                                "--run-id",
                                "run-1",
                                "--max-cycles",
                                "3",
                            ]
                        )

        output = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "awaiting_confirmation")
        self.assertEqual(output["cycle"], 1)

    def test_auto_recover_no_action_without_watch_exits_zero_without_sleep(self) -> None:
        summaries = [{"status": "no_action"}]

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                return summaries.pop(0)

        buffer = StringIO()
        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load", return_value=object()):
                with patch("labscriptai.runtime.cli._mcp_adapter"):
                    with patch("labscriptai.runtime.cli.time.sleep") as sleep:
                        with patch("sys.stdout", buffer):
                            exit_code = runtime_cli_main(
                                [
                                    "auto-recover",
                                    "--robot-ip",
                                    "10.0.0.2",
                                    "--run-id",
                                    "run-1",
                                ]
                            )

        output = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "no_action")
        sleep.assert_not_called()

    def test_auto_recover_watch_sleeps_after_no_action_and_catches_fault(self) -> None:
        summaries = [
            {"status": "no_action"},
            {"status": "succeeded", "execution": {"data": {"final_run_history": {"status": "succeeded"}}}},
        ]

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                return summaries.pop(0)

        buffer = StringIO()
        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load", return_value=object()):
                with patch("labscriptai.runtime.cli._mcp_adapter"):
                    with patch("labscriptai.runtime.cli.time.sleep") as sleep:
                        with patch("sys.stdout", buffer):
                            exit_code = runtime_cli_main(
                                [
                                    "auto-recover",
                                    "--robot-ip",
                                    "10.0.0.2",
                                    "--run-id",
                                    "run-1",
                                    "--watch",
                                    "--max-cycles",
                                    "3",
                                    "--poll-interval-sec",
                                    "0.25",
                                ]
                            )

        outputs = _decode_json_stream(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual([output["status"] for output in outputs], ["no_action", "succeeded"])
        sleep.assert_called_once_with(0.25)

    def test_auto_recover_mcp_error_retries_then_returns_nonzero(self) -> None:
        calls = 0

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                nonlocal calls
                calls += 1
                return {"status": "mcp_error", "errors": [{"source": "robot_status"}]}

        buffer = StringIO()
        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load", return_value=object()):
                with patch("labscriptai.runtime.cli._mcp_adapter"):
                    with patch("labscriptai.runtime.cli.time.sleep") as sleep:
                        with patch("sys.stdout", buffer):
                            exit_code = runtime_cli_main(
                                [
                                    "auto-recover",
                                    "--robot-ip",
                                    "10.0.0.2",
                                    "--run-id",
                                    "run-1",
                                    "--max-mcp-retries",
                                    "2",
                                ]
                            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(calls, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [5.0, 10.0])
        self.assertEqual(len(_decode_json_stream(buffer.getvalue())), 3)

    def test_auto_recover_stops_when_attempt_limit_is_reached(self) -> None:
        calls = 0

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                nonlocal calls
                calls += 1
                return {"status": "failed", "attempt": {"attempt_id": f"a-{calls}"}}

        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load", return_value=object()):
                with patch("labscriptai.runtime.cli._mcp_adapter"):
                    with patch("sys.stdout", new_callable=StringIO):
                        exit_code = runtime_cli_main(
                            [
                                "auto-recover",
                                "--robot-ip",
                                "10.0.0.2",
                                "--run-id",
                                "run-1",
                                "--auto-execute",
                                "--max-attempts",
                                "1",
                                "--max-cycles",
                                "3",
                            ]
                        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(calls, 1)

    def test_auto_recover_execute_mode_stops_on_success(self) -> None:
        summaries = [
            {"status": "succeeded", "execution": {"data": {"final_run_history": {"status": "succeeded"}}}},
        ]

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                return summaries.pop(0)

        buffer = StringIO()
        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load") as load_queue:
                with patch("labscriptai.runtime.cli._mcp_adapter") as mcp_adapter:
                    adapter = mcp_adapter.return_value
                    adapter.recovery_snapshot.return_value = {"parse_error": {"data": {}}}
                    adapter.state_from_snapshot.return_value = object()
                    load_queue.return_value = object()
                    with patch("sys.stdout", buffer):
                        exit_code = runtime_cli_main(
                            [
                                "auto-recover",
                                "--robot-ip",
                                "10.0.0.2",
                                "--run-id",
                                "run-1",
                                "--auto-execute",
                                "--max-cycles",
                                "3",
                            ]
                        )

        output = json.loads(buffer.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(output["status"], "succeeded")

    def test_auto_recover_blocked_returns_nonzero(self) -> None:
        summaries = [{"status": "blocked", "decision": {"status": "blocked"}}]

        class FakeOrchestrator:
            def __init__(self, **kwargs):  # noqa: ANN003
                del kwargs

            def step(self) -> dict:
                return summaries.pop(0)

        with patch("labscriptai.runtime.cli.RecoveryOrchestrator", FakeOrchestrator):
            with patch("labscriptai.runtime.cli.RecoveryQueue.load", return_value=object()):
                with patch("labscriptai.runtime.cli._mcp_adapter") as mcp_adapter:
                    adapter = mcp_adapter.return_value
                    adapter.recovery_snapshot.return_value = {"parse_error": {"data": {}}}
                    adapter.state_from_snapshot.return_value = object()
                    with patch("sys.stdout", new_callable=StringIO):
                        exit_code = runtime_cli_main(
                            [
                                "auto-recover",
                                "--robot-ip",
                                "10.0.0.2",
                                "--run-id",
                                "run-1",
                            ]
                        )

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
