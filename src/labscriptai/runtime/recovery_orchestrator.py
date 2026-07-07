"""Auto-recovery orchestrator: poll, suggest, gate, execute."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .actions import CandidateAction
from .adapters.mcp import snapshot_errors
from .gatekeeper import evaluate_action
from .memory import append_memory_note, count_branch_outcomes, search_memory
from .recovery_queue import RecoveryQueue
from .state import RuntimeState


def _unwrap(payload: Any) -> dict[str, Any]:
    if isinstance(payload, Mapping):
        data = payload.get("data")
        return dict(data) if isinstance(data, Mapping) else dict(payload)
    return {}


def _failed_command_id(parsed_error: Mapping[str, Any]) -> str:
    failed = parsed_error.get("failed_command")
    if isinstance(failed, Mapping):
        return str(failed.get("id") or "")
    return ""


def _branch(recovery: Mapping[str, Any]) -> str:
    return str(recovery.get("action") or recovery.get("recovery_branch") or "")


def _error_leaf(parsed_error: Mapping[str, Any]) -> str:
    return str(parsed_error.get("error_leaf") or "").strip()


def _memory_query(parsed_error: Mapping[str, Any], branch: str, failed_command_id: str) -> str:
    return " ".join(
        part
        for part in (
            _error_leaf(parsed_error),
            branch,
            failed_command_id,
        )
        if part
    )


def _inject_error_observation(
    state: RuntimeState,
    *,
    parsed_error: Mapping[str, Any],
    memory_hits: list[dict[str, Any]],
    branch: str = "",
    recovery: Mapping[str, Any] | None = None,
) -> RuntimeState:
    """Merge runtime error context and memory hits into the live observation."""

    observed: dict[str, Any] = {
        **dict(state.observed),
        "parsed_error": dict(parsed_error),
        "memory_hits": memory_hits,
    }
    error_leaf = _error_leaf(parsed_error)
    if error_leaf:
        observed["error_leaf"] = error_leaf
    if branch:
        observed["recovery_branch"] = branch
    if recovery:
        observed["recovery"] = dict(recovery)
    return state.with_observation(observed)


@dataclass
class RecoveryOrchestratorConfig:
    auto_execute: bool = False
    max_cycles: int = 3
    poll_interval_sec: float = 5
    max_watch_sec: float = 0
    memory_dir: Path | None = None
    memory_min_samples: int = 3
    memory_fail_rate: float = 0.6
    session_id: str | None = None


class RecoveryOrchestrator:
    def __init__(
        self,
        *,
        adapter: Any,
        robot_ip: str,
        run_id: str,
        queue: RecoveryQueue,
        state: RuntimeState,
        config: RecoveryOrchestratorConfig,
    ) -> None:
        self.adapter = adapter
        self.robot_ip = robot_ip
        self.run_id = run_id
        self.queue = queue
        self.state = state
        self.config = config

    def step(self) -> dict[str, Any]:
        snapshot = self.adapter.recovery_snapshot(robot_ip=self.robot_ip, run_id=self.run_id)
        errors = snapshot_errors(snapshot)
        if errors:
            return {"status": "mcp_error", "snapshot": snapshot, "errors": errors}

        autonomy_mode = str(self.state.expected.get("autonomy_mode", "auto"))
        self.state = self.adapter.state_from_snapshot(
            robot_ip=self.robot_ip,
            run_id=self.run_id,
            snapshot=snapshot,
            autonomy_mode=autonomy_mode,
        )
        parsed_error = _unwrap(snapshot.get("parse_error"))
        suggestion = snapshot.get("suggest_recovery_action")
        recovery = _unwrap(suggestion)
        branch = _branch(recovery)
        failed_command_id = _failed_command_id(parsed_error)
        error_leaf = _error_leaf(parsed_error)

        memory_hits: list[dict[str, Any]] = []
        if error_leaf and self.config.memory_dir is not None:
            memory_hits = [
                hit.to_dict()
                for hit in search_memory(
                    self.config.memory_dir,
                    _memory_query(parsed_error, branch, failed_command_id),
                )
            ]
            self.state = _inject_error_observation(
                self.state,
                parsed_error=parsed_error,
                memory_hits=memory_hits,
                branch=branch,
                recovery=recovery if branch else None,
            )

        if not branch:
            return {
                "status": "no_action",
                "snapshot": snapshot,
                "parsed_error": parsed_error,
                "memory_hits": memory_hits,
            }

        action = CandidateAction(
            action_type="execute_recovery_branch",
            reason=f"Execute MCP-supported recovery branch {branch}.",
            parameters={"branch": branch, "human_confirmed": self.config.auto_execute},
            proposed_by="recovery_orchestrator",
        )
        decision = evaluate_action(action, self.state)

        if not decision.approved:
            return {
                "status": "escalated" if decision.escalated else "blocked",
                "decision": decision.to_dict(),
                "parsed_error": parsed_error,
                "recovery": recovery,
                "memory_hits": memory_hits,
            }

        if self.config.auto_execute and recovery.get("auto_executable") is False:
            return {
                "status": "escalated",
                "reasons": ("recovery branch is not auto_executable",),
                "decision": decision.to_dict(),
                "parsed_error": parsed_error,
                "recovery": recovery,
                "memory_hits": memory_hits,
            }

        can_attempt, reasons = self.queue.can_attempt(
            run_id=self.run_id,
            failed_command_id=failed_command_id,
            branch=branch,
        )
        if not can_attempt:
            return {
                "status": "escalated",
                "reasons": list(reasons),
                "parsed_error": parsed_error,
                "recovery": recovery,
                "memory_hits": memory_hits,
            }

        memory_outcomes: dict[str, int] | None = None
        if self.config.memory_dir is not None:
            memory_outcomes = count_branch_outcomes(
                self.config.memory_dir,
                branch,
                error_leaf=str(parsed_error.get("error_leaf") or "") or None,
            )
            total = memory_outcomes["total"]
            fails = memory_outcomes["fails"]
            fail_rate = fails / total if total else 0.0
            if total >= self.config.memory_min_samples and fail_rate >= self.config.memory_fail_rate:
                return {
                    "status": "escalated",
                    "reasons": [
                        (
                            "memory outcome gate blocked branch "
                            f"{branch}: {fails}/{total} prior outcomes failed"
                        )
                    ],
                    "decision": decision.to_dict(),
                    "parsed_error": parsed_error,
                    "recovery": recovery,
                    "memory_hits": memory_hits,
                    "memory_outcomes": memory_outcomes,
                }

        if not self.config.auto_execute:
            return {
                "status": "awaiting_confirmation",
                "decision": decision.to_dict(),
                "parsed_error": parsed_error,
                "recovery": recovery,
                "memory_hits": memory_hits,
                "memory_outcomes": memory_outcomes,
                "preview": {
                    "branch": branch,
                    "failed_command_id": failed_command_id,
                    "error_leaf": parsed_error.get("error_leaf"),
                    "auto_executable": recovery.get("auto_executable"),
                },
            }

        attempt = self.queue.begin_attempt(
            run_id=self.run_id,
            failed_command_id=failed_command_id,
            error_leaf=str(parsed_error.get("error_leaf") or "UNKNOWN_NEEDS_HUMAN"),
            branch=branch,
            gatekeeper_status=decision.status,
        )

        extra_arguments: dict[str, Any] = {"idempotency_key": attempt.idempotency_key}
        if self.config.session_id:
            extra_arguments["session_id"] = self.config.session_id

        result = self.adapter.execute_suggested_recovery(
            robot_ip=self.robot_ip,
            run_id=self.run_id,
            suggestion=suggestion,
            extra_arguments=extra_arguments,
        )
        final_status = _unwrap(result.get("data", result)).get("final_run_history", {}).get("status")
        status = "succeeded" if final_status == "succeeded" and not result.get("error") else "failed"
        self.queue.finish_attempt(attempt.attempt_id, status=status, result=result)

        if self.config.memory_dir is not None:
            append_memory_note(
                self.config.memory_dir,
                title=f"{parsed_error.get('error_leaf', 'runtime')} recovery {branch}: {status}",
                body=(
                    f"run_id={self.run_id}\n"
                    f"failed_command_id={failed_command_id}\n"
                    f"branch={branch}\n"
                    f"status={status}"
                ),
                tags=("runtime", "recovery", str(parsed_error.get("error_leaf", "unknown"))),
                metadata={
                    "run_id": self.run_id,
                    "branch": branch,
                    "error_leaf": str(parsed_error.get("error_leaf") or "UNKNOWN_NEEDS_HUMAN"),
                    "status": status,
                },
            )

        return {
            "status": status,
            "attempt": attempt.to_dict(),
            "decision": decision.to_dict(),
            "parsed_error": parsed_error,
            "recovery": recovery,
            "execution": result,
            "memory_hits": memory_hits,
            "memory_outcomes": memory_outcomes,
        }
