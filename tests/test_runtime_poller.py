from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.chat_controller import ChatMessage, ChatResponse
from labscriptai.runtime.poller import RuntimePoller
from labscriptai.runtime.state import RuntimeState


class FakeRobotAdapter:
    def __init__(self) -> None:
        self.snapshots = [
            {"robot_health": {"robot_serial": "FLX-1"}, "run_history": {"run_id": "run-1", "status": "running"}},
            {
                "robot_health": {"robot_serial": "FLX-1"},
                "run_history": {
                    "run_id": "run-1",
                    "status": "running",
                    "completed_commands": [{"id": "cmd-1"}],
                },
            },
            {
                "robot_health": {"robot_serial": "FLX-1"},
                "run_history": {
                    "run_id": "run-1",
                    "status": "awaiting-recovery",
                    "completed_commands": [{"id": "cmd-1"}],
                    "failed_commands": [{"id": "cmd-2", "status": "failed"}],
                },
            },
        ]

    def snapshot(self, *, run_id: str | None = None):  # noqa: ANN201
        del run_id
        return self.snapshots.pop(0)

    def state_from_snapshot(self, *, run_id: str, snapshot):  # noqa: ANN001, ANN201
        history = snapshot["run_history"]
        status = history["status"]
        phase = "recovering" if status == "awaiting-recovery" else "running"
        return RuntimeState(
            run_id=run_id,
            phase=phase,
            robot={"id": "FLX-1"},
            observed=snapshot,
            completed_commands=tuple(history.get("completed_commands") or ()),
            failed_commands=tuple(history.get("failed_commands") or ()),
        )


class RuntimePollerTests(unittest.TestCase):
    def test_poller_wakes_model_only_on_abnormal_event(self) -> None:
        wake_prompts: list[str] = []

        def wake_handler(prompt: str, language: str) -> ChatResponse:
            wake_prompts.append(prompt)
            return ChatResponse((ChatMessage("assistant", "labscriptAI", (f"wake:{language}",)),))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            poller = RuntimePoller(
                adapter=FakeRobotAdapter(),
                run_id="run-1",
                trace_path=root / "trace.jsonl",
                wake_handler=wake_handler,
            )

            first = poller.poll_and_wake()
            second = poller.poll_and_wake()
            third = poller.poll_and_wake()
            events = [
                json.loads(line)
                for line in (root / "trace.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(first.responses, ())
        self.assertEqual(second.responses, ())
        self.assertEqual(len(third.responses), 1)
        self.assertEqual(len(wake_prompts), 1)
        self.assertTrue(any(event["event_type"] == "observation" for event in events))
        self.assertTrue(any(event["event_type"] == "runtime_event" for event in events))


if __name__ == "__main__":
    unittest.main()
