from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.runtime.agent_loop import (
    ScriptedCandidateProvider,
    run_offline_loop,
)
from labscriptai.runtime.state import RuntimeState
from labscriptai.runtime.trace import TraceWriter
from test_package_validator import write_valid_package


class AgentLoopTests(unittest.TestCase):
    def test_offline_loop_records_approved_read_only_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            trace_path = root / "trace.jsonl"

            result = run_offline_loop(
                initial_state=RuntimeState(run_id="run-1"),
                package_dir=package_dir,
                trace_path=trace_path,
                candidate_provider=ScriptedCandidateProvider(
                    [
                        {
                            "action_type": "simulate_protocol",
                            "reason": "Double-check the protocol package before execution.",
                        }
                    ]
                ),
                simulation_pass=True,
            )

            events = TraceWriter(trace_path).read_events()

        self.assertTrue(result.completed)
        self.assertEqual(result.final_state.phase, "ready")
        self.assertEqual(result.decisions[0].status, "approved")
        self.assertEqual(events[0]["event_type"], "tool_result")
        self.assertTrue(
            any(event["event_type"] == "gatekeeper_decision" for event in events)
        )
        self.assertEqual(events[-1]["event_type"], "summary")

    def test_offline_loop_blocks_direct_robot_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            trace_path = root / "trace.jsonl"

            result = run_offline_loop(
                initial_state=RuntimeState(
                    run_id="run-1",
                    phase="running",
                    robot={"id": "FLX-1"},
                ),
                package_dir=package_dir,
                trace_path=trace_path,
                candidate_provider=ScriptedCandidateProvider(
                    [
                        {
                            "action_type": "aspirate",
                            "reason": "This should be blocked.",
                            "parameters": {"well": "A1", "volume_ul": 10},
                        }
                    ]
                ),
                simulation_pass=True,
            )

            events = TraceWriter(trace_path).read_events()
            decision_events = [
                event
                for event in events
                if event["event_type"] == "gatekeeper_decision"
            ]

        self.assertFalse(result.completed)
        self.assertEqual(result.final_state.phase, "paused")
        self.assertEqual(result.decisions[0].status, "blocked")
        self.assertEqual(decision_events[-1]["payload"]["status"], "blocked")
        self.assertTrue(
            any(event["event_type"] == "escalation" for event in events)
        )

    def test_validation_failure_prevents_completed_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            (package_dir / "runbook.md").unlink()
            trace_path = root / "trace.jsonl"

            result = run_offline_loop(
                initial_state=RuntimeState(run_id="run-1"),
                package_dir=package_dir,
                trace_path=trace_path,
                candidate_provider=ScriptedCandidateProvider(
                    [
                        {
                            "action_type": "simulate_protocol",
                            "reason": "Try to validate despite package failure.",
                        }
                    ]
                ),
                simulation_pass=True,
            )

            events = TraceWriter(trace_path).read_events()

        self.assertFalse(result.completed)
        self.assertEqual(result.final_state.phase, "paused")
        self.assertFalse(events[0]["payload"]["result"]["ok"])

    def test_offline_loop_records_invalid_candidate_as_blocked_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            trace_path = root / "trace.jsonl"

            result = run_offline_loop(
                initial_state=RuntimeState(run_id="run-1"),
                package_dir=package_dir,
                trace_path=trace_path,
                candidate_provider=ScriptedCandidateProvider(
                    [{"reason": "missing action_type"}]
                ),
                simulation_pass=True,
            )

            events = TraceWriter(trace_path).read_events()

        self.assertFalse(result.completed)
        self.assertEqual(result.decisions, ())
        self.assertTrue(
            any(
                event["event_type"] == "gatekeeper_decision"
                and event["payload"]["status"] == "blocked"
                for event in events
            )
        )


if __name__ == "__main__":
    unittest.main()
