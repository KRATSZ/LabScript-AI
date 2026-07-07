from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.agent.loop import LabscriptAgentLoop, resume_loop
from labscriptai.agent.registry import build_default_registry
from labscriptai.agent.state import AgentState, PackageRef, TaskSpec
from labscriptai.agent.suspend import SuspendStore
from labscriptai.runtime.trace import TraceWriter


class ScriptedClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0

    def complete(self, messages, tools):
        del messages, tools
        self.input_tokens += 1
        self.output_tokens += 1
        self.total_tokens += 2
        return next(self.responses)


def _run_state(root: Path) -> AgentState:
    return AgentState(
        run_id="run-1",
        mode="run",
        phase="recovering",
        task_spec=TaskSpec(task_id="R001", prompt="resume after recovery"),
        package=PackageRef.from_dir(root / "package"),
        trace_path=root / "trace.jsonl",
        trace=TraceWriter(root / "trace.jsonl"),
        permissions=frozenset(),
        robot_status={"id": "FLX-1", "host": "127.0.0.1"},
    )


class AgentLoopSuspendTests(unittest.TestCase):
    def test_escalated_run_control_suspends_and_resumes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _run_state(root)
            client = ScriptedClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": "run.control",
                                "reason": "Resume after recovery.",
                                "arguments": {"action_type": "resume_run"},
                            }
                        ]
                    },
                    {"final": {"completed": True}},
                ]
            )
            store = SuspendStore()
            loop = LabscriptAgentLoop(
                client=client,
                registry=build_default_registry(),
                max_steps=3,
                suspend_store=store,
                suspend_dir=root / "suspended",
            )

            result = loop.run(state)

            self.assertTrue(result.suspended)
            self.assertIsNotNone(result.suspend_id)
            self.assertFalse(result.completed)
            self.assertEqual(result.final_state.phase, "recovering")
            self.assertIsNotNone(loop.last_tool_results[-1].decision)
            self.assertTrue(loop.last_tool_results[-1].decision.escalated)
            self.assertTrue((root / "suspended" / f"{result.suspend_id}.json").exists())

            events = [
                json.loads(line)
                for line in (root / "trace.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertTrue(any(event["event_type"] == "escalation" for event in events))
            self.assertTrue(events[-1]["payload"]["suspended"])

            resumed = resume_loop(loop, result.suspend_id, {"human_confirmed": True})

            self.assertFalse(resumed.suspended)
            self.assertTrue(resumed.completed)
            self.assertEqual(resumed.final_state.phase, "completed")
            self.assertTrue(loop.last_tool_results[-1].ok)
            self.assertTrue(loop.last_tool_results[-1].decision.approved)
            self.assertTrue(any(message["role"] == "system" for message in loop.messages))
            self.assertFalse((root / "suspended" / f"{result.suspend_id}.json").exists())

    def test_resume_loop_requires_human_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _run_state(root)
            client = ScriptedClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": "run.control",
                                "reason": "Resume after recovery.",
                                "arguments": {"action_type": "resume_run"},
                            }
                        ]
                    }
                ]
            )
            loop = LabscriptAgentLoop(
                client=client,
                registry=build_default_registry(),
                max_steps=1,
                suspend_dir=root / "suspended",
            )
            result = loop.run(state)
            self.assertTrue(result.suspended)
            self.assertIsNotNone(result.suspend_id)

            with self.assertRaisesRegex(ValueError, "human_confirmed"):
                loop.resume_loop(result.suspend_id, {"human_confirmed": False})

    def test_suspend_snapshot_round_trip_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _run_state(root)
            client = ScriptedClient(
                [
                    {
                        "tool_calls": [
                            {
                                "name": "run.control",
                                "reason": "Resume after recovery.",
                                "arguments": {"action_type": "resume_run"},
                            }
                        ]
                    }
                ]
            )
            suspend_dir = root / "suspended"
            loop_a = LabscriptAgentLoop(
                client=client,
                registry=build_default_registry(),
                max_steps=1,
                suspend_store=SuspendStore(),
                suspend_dir=suspend_dir,
            )
            suspended = loop_a.run(state)
            self.assertIsNotNone(suspended.suspend_id)

            loop_b = LabscriptAgentLoop(
                client=ScriptedClient([{"final": {"completed": True}}]),
                registry=build_default_registry(),
                max_steps=2,
                suspend_store=SuspendStore(),
                suspend_dir=suspend_dir,
            )
            resumed = loop_b.resume_loop(suspended.suspend_id, {"human_confirmed": True})

            self.assertFalse(resumed.suspended)
            self.assertEqual(resumed.final_state.run_id, "run-1")


if __name__ == "__main__":
    unittest.main()
