from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.actions import CandidateAction
from labscriptai.runtime.gatekeeper import evaluate_action
from labscriptai.runtime.state import RuntimeRisk, RuntimeState
from labscriptai.runtime.trace import TraceEvent, TraceWriter


class RuntimeGatekeeperTests(unittest.TestCase):
    def test_read_only_action_is_approved_without_robot_identity(self) -> None:
        state = RuntimeState(run_id="run-1", phase="preflight")
        action = CandidateAction(
            action_type="simulate_protocol",
            reason="Check the protocol before any robot interaction.",
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.approved)
        self.assertEqual(decision.status, "approved")

    def test_forbidden_robot_motion_is_blocked(self) -> None:
        state = RuntimeState(run_id="run-1", phase="running", robot={"id": "FLX-1"})
        action = CandidateAction(
            action_type="aspirate",
            reason="Model should never directly aspirate.",
            parameters={"well": "A1", "volume_ul": 10},
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertIn("forbidden action type", decision.reasons[0])

    def test_hardware_action_requires_robot_identity(self) -> None:
        state = RuntimeState(run_id="run-1", phase="running")
        action = CandidateAction(
            action_type="pause_run",
            reason="Pause after unexpected deck observation.",
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertIn("robot identity", decision.reasons[0])

    def test_resume_run_requires_human_confirmation(self) -> None:
        state = RuntimeState(run_id="run-1", phase="recovering", robot={"id": "FLX-1"})
        action = CandidateAction(
            action_type="resume_run",
            reason="Resume after recovery.",
            parameters={"human_confirmed": False},
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.escalated)
        self.assertIn("human_confirmed", decision.reasons[0])

    def test_resume_run_with_blocker_is_blocked_before_human_confirmation(self) -> None:
        state = RuntimeState(
            run_id="run-1",
            phase="recovering",
            robot={"id": "FLX-1"},
            risks=(
                RuntimeRisk(
                    code="deck_conflict",
                    severity="blocker",
                    message="Destination slot is occupied.",
                ),
            ),
        )
        action = CandidateAction(
            action_type="resume_run",
            reason="Resume after recovery.",
            parameters={"human_confirmed": False},
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertTrue(any("deck_conflict" in reason for reason in decision.reasons))

    def test_blocker_risk_blocks_moving_recovery_action(self) -> None:
        state = RuntimeState(
            run_id="run-1",
            phase="recovering",
            robot={"id": "FLX-1"},
            risks=(
                RuntimeRisk(
                    code="deck_conflict",
                    severity="blocker",
                    message="Destination slot is occupied.",
                ),
            ),
        )
        action = CandidateAction(
            action_type="abort_run",
            reason="Abort after blocked recovery.",
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertTrue(any("deck_conflict" in reason for reason in decision.reasons))

    def test_action_from_mapping_requires_parameters_object(self) -> None:
        with self.assertRaises(ValueError):
            CandidateAction.from_mapping(
                {"action_type": "simulate_protocol", "reason": "x", "parameters": []}
            )

    def test_human_confirmation_message_is_normalized_to_question(self) -> None:
        action = CandidateAction.from_mapping(
            {
                "action_type": "request_human_confirmation",
                "reason": "Need setup confirmation.",
                "parameters": {"message": "Confirm deck layout?"},
            }
        )

        self.assertEqual(action.parameters["question"], "Confirm deck layout?")

    def test_trace_writer_persists_state_hashed_events(self) -> None:
        state = RuntimeState(run_id="run-1", phase="preflight")
        event = TraceEvent.for_state(
            state,
            event_type="candidate_action",
            actor="model",
            payload={"action_type": "simulate_protocol"},
        )

        with tempfile.TemporaryDirectory() as tmp:
            trace_path = Path(tmp) / "trace.jsonl"
            writer = TraceWriter(trace_path)
            writer.append(event)
            events = writer.read_events()

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["run_id"], "run-1")
        self.assertEqual(events[0]["event_type"], "candidate_action")
        self.assertEqual(events[0]["state_hash"], state.stable_hash())


if __name__ == "__main__":
    unittest.main()
