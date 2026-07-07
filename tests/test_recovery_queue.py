from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.runtime.recovery_queue import RecoveryAttempt, RecoveryQueue


class RecoveryQueueTests(unittest.TestCase):
    def _old_running_attempt(self, *, now: datetime, seconds_old: int) -> RecoveryAttempt:
        return RecoveryAttempt(
            attempt_id=f"a-{seconds_old}",
            run_id="run-1",
            failed_command_id="cmd-1",
            error_leaf="TIP_PHYSICALLY_MISSING",
            branch="retry_pick_up_tip_with_next_candidate",
            idempotency_key=f"key-{seconds_old}",
            status="running",
            started_at=(now - timedelta(seconds=seconds_old)).isoformat().replace("+00:00", "Z"),
        )

    def test_queue_persists_and_reloads_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            queue = RecoveryQueue.load(path)
            attempt = queue.begin_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                error_leaf="TIP_PHYSICALLY_MISSING",
                branch="retry_pick_up_tip_with_next_candidate",
                gatekeeper_status="approved",
            )
            queue.finish_attempt(attempt.attempt_id, status="succeeded", result={"ok": True})

            reloaded = RecoveryQueue.load(path)
            self.assertEqual(len(reloaded.attempts), 1)
            self.assertEqual(reloaded.attempts[0].status, "succeeded")
            self.assertEqual(reloaded.attempts[0].result, {"ok": True})

    def test_begin_attempt_creates_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            queue = RecoveryQueue.load(path)
            attempt = queue.begin_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                error_leaf="TIP_PHYSICALLY_MISSING",
                branch="retry_pick_up_tip_with_next_candidate",
                gatekeeper_status="approved",
            )
            self.assertEqual(len(attempt.idempotency_key), 24)
            self.assertEqual(attempt.status, "running")

    def test_retry_budget_blocks_after_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            queue = RecoveryQueue.load(path, max_attempts_per_failed_command=2)
            for _ in range(2):
                attempt = queue.begin_attempt(
                    run_id="run-1",
                    failed_command_id="cmd-1",
                    error_leaf="TIP_PHYSICALLY_MISSING",
                    branch="retry_pick_up_tip_with_next_candidate",
                    gatekeeper_status="approved",
                )
                queue.finish_attempt(attempt.attempt_id, status="failed", result={})

            can_attempt, reasons = queue.can_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                branch="retry_pick_up_tip_with_next_candidate",
            )
            self.assertFalse(can_attempt)
            self.assertTrue(any("retry budget exhausted" in reason for reason in reasons))

    def test_running_duplicate_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            queue = RecoveryQueue.load(path)
            queue.begin_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                error_leaf="TIP_PHYSICALLY_MISSING",
                branch="retry_pick_up_tip_with_next_candidate",
                gatekeeper_status="approved",
            )
            can_attempt, reasons = queue.can_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                branch="retry_pick_up_tip_with_next_candidate",
            )
            self.assertFalse(can_attempt)
            self.assertTrue(any("already running" in reason for reason in reasons))

    def test_stale_running_attempt_is_reaped_and_counts_against_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            queue = RecoveryQueue.load(path, max_attempts_per_failed_command=2)
            queue.attempts.append(self._old_running_attempt(now=now, seconds_old=1801))
            queue.save()

            can_attempt, reasons = queue.can_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                branch="retry_pick_up_tip_with_next_candidate",
                now=now,
            )

            self.assertTrue(can_attempt)
            self.assertEqual(reasons, ())
            self.assertEqual(queue.attempts[0].status, "failed")
            self.assertEqual(queue.attempts[0].result, {"result": "stale_running_reaped"})

            attempt = queue.begin_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                error_leaf="TIP_PHYSICALLY_MISSING",
                branch="retry_pick_up_tip_with_next_candidate",
                gatekeeper_status="approved",
            )
            queue.finish_attempt(attempt.attempt_id, status="failed", result={})

            can_attempt, reasons = queue.can_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                branch="retry_pick_up_tip_with_next_candidate",
                now=now,
            )
            self.assertFalse(can_attempt)
            self.assertTrue(any("retry budget exhausted" in reason for reason in reasons))

    def test_fresh_running_attempt_is_not_reaped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            queue = RecoveryQueue.load(path)
            queue.attempts.append(self._old_running_attempt(now=now, seconds_old=1799))
            queue.save()

            can_attempt, reasons = queue.can_attempt(
                run_id="run-1",
                failed_command_id="cmd-1",
                branch="retry_pick_up_tip_with_next_candidate",
                now=now,
            )

            self.assertFalse(can_attempt)
            self.assertEqual(queue.attempts[0].status, "running")
            self.assertTrue(any("already running" in reason for reason in reasons))

    def test_attempt_round_trip(self) -> None:
        attempt = RecoveryAttempt(
            attempt_id="a-1",
            run_id="run-1",
            failed_command_id="cmd-1",
            error_leaf="TIP_PHYSICALLY_MISSING",
            branch="retry_pick_up_tip_with_next_candidate",
            idempotency_key="abc123",
        )
        restored = RecoveryAttempt.from_mapping(attempt.to_dict())
        self.assertEqual(restored.attempt_id, attempt.attempt_id)
        self.assertEqual(restored.branch, attempt.branch)


if __name__ == "__main__":
    unittest.main()
