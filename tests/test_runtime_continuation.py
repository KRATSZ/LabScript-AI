from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from labscriptai.runtime.actions import CandidateAction
from labscriptai.runtime.agent_loop import ScriptedCandidateProvider, run_offline_loop
from labscriptai.runtime.continuation import (
    build_ledger_from_run_history,
    validate_continuation_patch,
)
from labscriptai.runtime.gatekeeper import evaluate_action
from labscriptai.runtime.patch_log import PatchLogWriter
from labscriptai.runtime.state import RuntimeState
from test_package_validator import write_valid_package


def valid_patch() -> dict:
    return {
        "schema_version": "0.1",
        "patch_id": "patch-1",
        "recovery_type": "continuation_protocol",
        "operations": [
            {
                "op_type": "transfer",
                "tip": "A2",
                "source_well": "reservoir:A2",
                "destination_well": "plate:B1",
                "reagent": "buffer",
                "volume_ul": 10,
            }
        ],
    }


class RuntimeContinuationTests(unittest.TestCase):
    def test_used_tip_is_blocked(self) -> None:
        state = RuntimeState(run_id="run-1", used_tips=("A2",))
        patch = valid_patch()

        result = validate_continuation_patch(patch, state)

        self.assertFalse(result.ok)
        self.assertTrue(any("used tip A2" in reason for reason in result.reasons))

    def test_duplicate_dispense_is_blocked(self) -> None:
        state = RuntimeState(
            run_id="run-1",
            treated_wells=("plate:B1",),
            liquid_transfers=(
                {
                    "source_well": "reservoir:A2",
                    "destination_well": "plate:B1",
                    "reagent": "buffer",
                    "volume_ul": 10,
                },
            ),
        )
        patch = valid_patch()

        result = validate_continuation_patch(patch, state)

        self.assertFalse(result.ok)
        self.assertTrue(any("already treated well plate:B1" in reason for reason in result.reasons))
        self.assertTrue(any("duplicates committed transfer" in reason for reason in result.reasons))

    def test_insufficient_source_volume_is_blocked(self) -> None:
        state = RuntimeState(
            run_id="run-1",
            observed={"source_volumes_ul": {"reservoir:A2": 5}},
        )
        patch = valid_patch()

        result = validate_continuation_patch(patch, state)

        self.assertFalse(result.ok)
        self.assertTrue(any("only 5.0uL observed" in reason for reason in result.reasons))

    def test_gatekeeper_blocks_unsafe_patch_action(self) -> None:
        state = RuntimeState(run_id="run-1", used_tips=("A2",))
        action = CandidateAction(
            action_type="validate_continuation_patch",
            reason="Check the remaining-steps patch before resume.",
            parameters={"patch": valid_patch()},
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertTrue(any("used tip A2" in reason for reason in decision.reasons))

    def test_gatekeeper_requires_human_confirmation_before_execution(self) -> None:
        state = RuntimeState(run_id="run-1", phase="recovering", robot={"id": "FLX-1"})
        patch = valid_patch()
        action = CandidateAction(
            action_type="execute_recovery_branch",
            reason="Execute the checked continuation patch.",
            parameters={"branch": "continuation_patch", "patch": patch},
        )

        decision = evaluate_action(action, state)

        self.assertTrue(decision.blocked)
        self.assertTrue(any("human_confirmed" in reason for reason in decision.reasons))

    def test_failed_command_ledger_from_run_history(self) -> None:
        ledger = build_ledger_from_run_history(
            {
                "recent_commands": [
                    {"id": "cmd-1", "command_type": "aspirate", "status": "succeeded"},
                    {"id": "cmd-2", "command_type": "dispense", "status": "failed"},
                    {"id": "cmd-3", "command_type": "dropTip", "status": "queued"},
                ]
            }
        )

        self.assertEqual(ledger["completed_commands"][0]["id"], "cmd-1")
        self.assertEqual(ledger["failed_commands"][0]["id"], "cmd-2")
        self.assertEqual(ledger["remaining_plan"][0]["id"], "cmd-3")

    def test_runtime_loop_writes_patch_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_dir = root / "package"
            package_dir.mkdir()
            write_valid_package(package_dir)
            trace_path = root / "trace.jsonl"
            patch_log_path = root / "patch_log.jsonl"

            result = run_offline_loop(
                initial_state=RuntimeState(run_id="run-1", phase="recovering", robot={"id": "FLX-1"}),
                package_dir=package_dir,
                trace_path=trace_path,
                patch_log_path=patch_log_path,
                candidate_provider=ScriptedCandidateProvider(
                    [
                        {
                            "action_type": "validate_continuation_patch",
                            "reason": "Validate breakpoint patch.",
                            "parameters": {"patch": valid_patch()},
                        }
                    ]
                ),
                simulation_pass=True,
            )
            entries = PatchLogWriter(patch_log_path).read_entries()

        self.assertTrue(result.completed)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["patch"]["patch_id"], "patch-1")
        self.assertEqual(entries[0]["gatekeeper_decision"]["status"], "approved")


if __name__ == "__main__":
    unittest.main()
