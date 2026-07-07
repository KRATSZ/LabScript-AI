from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from labscriptai.runtime.recovery_orchestrator import RecoveryOrchestrator, RecoveryOrchestratorConfig
from labscriptai.runtime.memory import append_memory_note
from labscriptai.runtime.recovery_queue import RecoveryQueue
from labscriptai.runtime.state import RuntimeState


class FakeMcpAdapter:
    def __init__(self, *, auto_executable: bool = True, snapshot: dict | None = None) -> None:
        self.auto_executable = auto_executable
        self.snapshot = snapshot
        self.executions: list[dict] = []

    def recovery_snapshot(self, *, robot_ip: str, run_id: str) -> dict:
        del robot_ip, run_id
        if self.snapshot is not None:
            return self.snapshot
        return {
            "parse_error": {
                "data": {
                    "error_leaf": "TIP_PHYSICALLY_MISSING",
                    "failed_command": {"id": "cmd-failed"},
                }
            },
            "suggest_recovery_action": {
                "data": {
                    "action": "retry_pick_up_tip_with_next_candidate",
                    "auto_executable": self.auto_executable,
                }
            },
        }

    def execute_suggested_recovery(self, *, robot_ip, run_id, suggestion, extra_arguments=None):  # noqa: ANN001
        del robot_ip, run_id, suggestion
        self.executions.append(dict(extra_arguments or {}))
        return {"data": {"final_run_history": {"status": "succeeded"}}}

    def state_from_snapshot(self, *, robot_ip, run_id, snapshot, autonomy_mode="auto"):  # noqa: ANN001
        del robot_ip, snapshot
        return RuntimeState(
            run_id=run_id,
            phase="recovering",
            robot={"host": "10.0.0.2", "id": "FLX-1"},
            expected={"autonomy_mode": autonomy_mode},
        )


class RecoveryOrchestratorTests(unittest.TestCase):
    def _orchestrator(
        self,
        *,
        path: Path,
        auto_execute: bool = True,
        memory_dir: Path | None = None,
    ) -> tuple[RecoveryOrchestrator, FakeMcpAdapter]:
        adapter = FakeMcpAdapter()
        state = RuntimeState(
            run_id="run-1",
            phase="recovering",
            robot={"host": "10.0.0.2", "id": "FLX-1"},
            expected={"autonomy_mode": "auto"},
        )
        orchestrator = RecoveryOrchestrator(
            adapter=adapter,
            robot_ip="10.0.0.2",
            run_id="run-1",
            queue=RecoveryQueue.load(path),
            state=state,
            config=RecoveryOrchestratorConfig(auto_execute=auto_execute, memory_dir=memory_dir),
        )
        return orchestrator, adapter

    def test_auto_execute_calls_adapter_with_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=True)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "succeeded")
            self.assertEqual(len(adapter.executions), 1)
            self.assertIn("idempotency_key", adapter.executions[0])
            self.assertEqual(len(adapter.executions[0]["idempotency_key"]), 24)

    def test_mcp_error_short_circuits_without_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            adapter = FakeMcpAdapter(
                snapshot={
                    "robot_status": {"error": "mcp_tool_failed", "tool": "robot_status"},
                    "module_status": {"data": {"ok": True}},
                    "parse_error": {"data": {"error_leaf": "TIP_PHYSICALLY_MISSING"}},
                    "suggest_recovery_action": {
                        "data": {"action": "retry_pick_up_tip_with_next_candidate"}
                    },
                }
            )
            orchestrator = RecoveryOrchestrator(
                adapter=adapter,
                robot_ip="10.0.0.2",
                run_id="run-1",
                queue=RecoveryQueue.load(path),
                state=RuntimeState(
                    run_id="run-1",
                    phase="recovering",
                    robot={"host": "10.0.0.2", "id": "FLX-1"},
                    expected={"autonomy_mode": "auto"},
                ),
                config=RecoveryOrchestratorConfig(auto_execute=True),
            )

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "mcp_error")
            self.assertEqual(summary["errors"][0]["source"], "robot_status")
            self.assertEqual(adapter.executions, [])
            self.assertEqual(RecoveryQueue.load(path).attempts, [])

    def test_shadow_mode_returns_awaiting_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=False)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "awaiting_confirmation")
            self.assertEqual(adapter.executions, [])
            self.assertNotIn("attempt", summary)
            self.assertEqual(RecoveryQueue.load(path).attempts, [])

    def test_shadow_mode_can_be_polled_repeatedly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=False)

            first = orchestrator.step()
            second = orchestrator.step()

            self.assertEqual(first["status"], "awaiting_confirmation")
            self.assertEqual(second["status"], "awaiting_confirmation")
            self.assertEqual(adapter.executions, [])
            self.assertEqual(RecoveryQueue.load(path).attempts, [])

    def test_non_auto_executable_branch_escalates_in_auto_execute_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            adapter = FakeMcpAdapter(auto_executable=False)
            orchestrator = RecoveryOrchestrator(
                adapter=adapter,
                robot_ip="10.0.0.2",
                run_id="run-1",
                queue=RecoveryQueue.load(path),
                state=RuntimeState(
                    run_id="run-1",
                    phase="recovering",
                    robot={"host": "10.0.0.2", "id": "FLX-1"},
                    expected={"autonomy_mode": "auto"},
                ),
                config=RecoveryOrchestratorConfig(auto_execute=True),
            )

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "escalated")
            self.assertEqual(adapter.executions, [])

    def test_memory_gate_escalates_repeated_failed_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.json"
            memory_dir = root / "memory"
            for index in range(3):
                append_memory_note(
                    memory_dir,
                    title=f"failed branch {index}",
                    body="prior failed recovery",
                    tags=("runtime", "recovery"),
                    metadata={
                        "branch": "retry_pick_up_tip_with_next_candidate",
                        "error_leaf": "TIP_PHYSICALLY_MISSING",
                        "status": "failed",
                    },
                )
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=True, memory_dir=memory_dir)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "escalated")
            self.assertEqual(summary["memory_outcomes"], {"total": 3, "fails": 3})
            self.assertEqual(adapter.executions, [])
            self.assertEqual(RecoveryQueue.load(path).attempts, [])

    def test_memory_gate_allows_low_or_insufficient_failure_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.json"
            memory_dir = root / "memory"
            append_memory_note(
                memory_dir,
                title="single failed branch",
                body="prior failed recovery",
                tags=("runtime", "recovery"),
                metadata={
                    "branch": "retry_pick_up_tip_with_next_candidate",
                    "error_leaf": "TIP_PHYSICALLY_MISSING",
                    "status": "failed",
                },
            )
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=True, memory_dir=memory_dir)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "succeeded")
            self.assertEqual(len(adapter.executions), 1)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.json"
            memory_dir = root / "memory"
            for status in ("failed", "succeeded", "succeeded"):
                append_memory_note(
                    memory_dir,
                    title=f"{status} branch",
                    body="prior recovery",
                    tags=("runtime", "recovery"),
                    metadata={
                        "branch": "retry_pick_up_tip_with_next_candidate",
                        "error_leaf": "TIP_PHYSICALLY_MISSING",
                        "status": status,
                    },
                )
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=True, memory_dir=memory_dir)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "succeeded")
            self.assertEqual(len(adapter.executions), 1)

    def test_gatekeeper_blocked_when_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            orchestrator, adapter = self._orchestrator(path=path, auto_execute=False)
            orchestrator.state = RuntimeState(
                run_id="run-1",
                phase="recovering",
                robot={"host": "10.0.0.2", "id": "FLX-1"},
                expected={"autonomy_mode": "conservative"},
            )

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "blocked")
            self.assertEqual(adapter.executions, [])

    def test_retry_budget_exhausted_returns_escalated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.json"
            queue = RecoveryQueue.load(path, max_attempts_per_failed_command=1)
            for _ in range(1):
                attempt = queue.begin_attempt(
                    run_id="run-1",
                    failed_command_id="cmd-failed",
                    error_leaf="TIP_PHYSICALLY_MISSING",
                    branch="retry_pick_up_tip_with_next_candidate",
                    gatekeeper_status="approved",
                )
                queue.finish_attempt(attempt.attempt_id, status="failed", result={})

            orchestrator, adapter = self._orchestrator(path=path, auto_execute=True)
            orchestrator.queue = queue

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "escalated")
            self.assertEqual(adapter.executions, [])

    def test_memory_note_written_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.json"
            memory_dir = root / "memory"
            orchestrator, _adapter = self._orchestrator(path=path, auto_execute=True, memory_dir=memory_dir)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "succeeded")
            notes = list(memory_dir.glob("*.md"))
            self.assertEqual(len(notes), 1)
            note = notes[0].read_text(encoding="utf-8")
            self.assertIn("TIP_PHYSICALLY_MISSING", note)
            self.assertIn("error_leaf: TIP_PHYSICALLY_MISSING", note)

    def test_error_observation_injects_memory_hits_without_tool_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "checkpoint.json"
            memory_dir = root / "memory"
            append_memory_note(
                memory_dir,
                title="missing tip recovery",
                body="retry with next candidate tip worked before",
                tags=("runtime", "recovery", "TIP_PHYSICALLY_MISSING"),
                metadata={
                    "branch": "retry_pick_up_tip_with_next_candidate",
                    "error_leaf": "TIP_PHYSICALLY_MISSING",
                    "status": "succeeded",
                },
            )
            orchestrator, _adapter = self._orchestrator(path=path, auto_execute=False, memory_dir=memory_dir)

            summary = orchestrator.step()

            self.assertEqual(summary["status"], "awaiting_confirmation")
            self.assertTrue(summary["memory_hits"])
            observed = orchestrator.state.observed
            self.assertEqual(observed["error_leaf"], "TIP_PHYSICALLY_MISSING")
            self.assertEqual(observed["memory_hits"], summary["memory_hits"])
            self.assertEqual(
                observed["recovery_branch"],
                "retry_pick_up_tip_with_next_candidate",
            )


if __name__ == "__main__":
    unittest.main()
