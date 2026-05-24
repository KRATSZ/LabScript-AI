from __future__ import annotations

import unittest

from labscriptai.runtime.events import RuntimeEventClassifier
from labscriptai.runtime.state import RuntimeState


def _snapshot(status: str) -> dict:
    return {"run_history": {"run_id": "run-1", "status": status}, "robot_health": {"robot_serial": "FLX-1"}}


class RuntimeEventClassifierTests(unittest.TestCase):
    def test_running_to_running_without_failure_does_not_wake_model(self) -> None:
        classifier = RuntimeEventClassifier()

        events = classifier.classify(
            _snapshot("running"),
            _snapshot("running"),
            RuntimeState(run_id="run-1", phase="running"),
            RuntimeState(run_id="run-1", phase="running"),
        )

        self.assertEqual(events, [])

    def test_running_to_succeeded_records_completion_without_wake(self) -> None:
        classifier = RuntimeEventClassifier()

        events = classifier.classify(
            _snapshot("running"),
            _snapshot("succeeded"),
            RuntimeState(run_id="run-1", phase="running"),
            RuntimeState(run_id="run-1", phase="completed"),
        )

        self.assertEqual(events[0].kind, "run_completed")
        self.assertFalse(events[0].should_wake_model)

    def test_new_failed_command_wakes_model(self) -> None:
        classifier = RuntimeEventClassifier()

        events = classifier.classify(
            _snapshot("running"),
            _snapshot("running"),
            RuntimeState(run_id="run-1", phase="running"),
            RuntimeState(run_id="run-1", phase="running", failed_commands=({"id": "cmd-1"},)),
        )

        self.assertEqual(events[0].kind, "command_failed")
        self.assertTrue(events[0].should_wake_model)
        self.assertIn("Runtime event detected", events[0].suggested_prompt)

    def test_awaiting_recovery_wakes_model(self) -> None:
        classifier = RuntimeEventClassifier()

        events = classifier.classify(
            _snapshot("running"),
            _snapshot("awaiting-recovery"),
            RuntimeState(run_id="run-1", phase="running"),
            RuntimeState(run_id="run-1", phase="recovering"),
        )

        self.assertEqual(events[0].kind, "awaiting_recovery")
        self.assertTrue(events[0].should_wake_model)

    def test_robot_unreachable_requires_three_consecutive_errors(self) -> None:
        classifier = RuntimeEventClassifier(robot_unreachable_threshold=3)

        first = classifier.classify_poll_error({"error": "down"}, run_id="run-1")
        second = classifier.classify_poll_error({"error": "down"}, run_id="run-1")
        third = classifier.classify_poll_error({"error": "down"}, run_id="run-1")

        self.assertEqual(first, [])
        self.assertEqual(second, [])
        self.assertEqual(third[0].kind, "robot_unreachable")
        self.assertTrue(third[0].should_wake_model)

    def test_repeated_abnormal_event_is_throttled_for_sixty_seconds(self) -> None:
        now = [100.0]
        classifier = RuntimeEventClassifier(now=lambda: now[0], wake_cooldown_sec=60.0)

        events = classifier.classify(
            _snapshot("running"),
            _snapshot("running"),
            RuntimeState(run_id="run-1", phase="running"),
            RuntimeState(run_id="run-1", phase="running", failed_commands=({"id": "cmd-1"},)),
        )
        first = classifier.mark_wake_allowed(events[0])
        repeated = classifier.mark_wake_allowed(events[0])
        now[0] = 161.0
        after_cooldown = classifier.mark_wake_allowed(events[0])

        self.assertTrue(first.should_wake_model)
        self.assertFalse(repeated.should_wake_model)
        self.assertTrue(after_cooldown.should_wake_model)


if __name__ == "__main__":
    unittest.main()
