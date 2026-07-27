"""Auto-recovery orchestrator: poll, suggest, gate, execute."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .actions import CandidateAction
from .adapters.mcp import snapshot_errors
from .current_policy import evaluate_runtime_action
from .gatekeeper import GatekeeperDecision, is_supported_recovery_branch
from .llm_queue_planner import CandidateProvider, suggest_action
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


def _merge_runtime_state(prior: RuntimeState, live: RuntimeState) -> RuntimeState:
    """Merge fresh MCP truth without dropping benchmark/global constraints."""

    risks = list(prior.risks)
    seen_risks = {(risk.code, risk.severity, risk.message) for risk in risks}
    for risk in live.risks:
        key = (risk.code, risk.severity, risk.message)
        if key not in seen_risks:
            risks.append(risk)
            seen_risks.add(key)
    return RuntimeState(
        schema_version=live.schema_version or prior.schema_version,
        run_id=live.run_id,
        phase=live.phase,
        robot={**dict(prior.robot), **dict(live.robot)},
        expected={**dict(prior.expected), **dict(live.expected)},
        committed={**dict(prior.committed), **dict(live.committed)},
        observed={**dict(prior.observed), **dict(live.observed)},
        completed_commands=live.completed_commands or prior.completed_commands,
        failed_commands=live.failed_commands or prior.failed_commands,
        used_tips=live.used_tips or prior.used_tips,
        treated_wells=live.treated_wells or prior.treated_wells,
        liquid_transfers=live.liquid_transfers or prior.liquid_transfers,
        remaining_plan=live.remaining_plan or prior.remaining_plan,
        risks=tuple(risks),
    )


def _deterministic_action(
    *,
    branch: str,
    human_confirmed: bool,
) -> CandidateAction:
    return CandidateAction(
        action_type="execute_recovery_branch",
        reason=f"Execute MCP-supported recovery branch {branch}.",
        parameters={"branch": branch, "human_confirmed": human_confirmed},
        proposed_by="mcp_suggest_recovery_action",
    )


def _deterministic_candidate_viable(
    *,
    recovery: Mapping[str, Any],
    branch: str,
    auto_execute: bool,
) -> bool:
    if not branch:
        return False
    if not is_supported_recovery_branch(branch):
        return False
    if auto_execute and recovery.get("auto_executable") is False:
        return False
    return True


def _action_branch(action: CandidateAction) -> str:
    if action.action_type != "execute_recovery_branch":
        return ""
    return str(action.parameters.get("branch") or "")


def _execution_suggestion(
    *,
    mcp_suggestion: Any,
    recovery: Mapping[str, Any],
    action: CandidateAction,
) -> Mapping[str, Any]:
    if action.proposed_by == "mcp_suggest_recovery_action" and isinstance(mcp_suggestion, Mapping):
        return mcp_suggestion
    branch = _action_branch(action)
    payload: dict[str, Any] = {"action": branch, "recovery_branch": branch}
    patch = action.parameters.get("patch")
    if isinstance(patch, Mapping):
        payload["patch"] = dict(patch)
    for key in ("recovery_well", "tiprack_slot", "failed_well", "destination_slot"):
        if key in action.parameters:
            payload[key] = action.parameters[key]
    if recovery:
        for key in ("recovery_well", "tiprack_slot", "failed_well", "destination_slot"):
            if key in recovery and key not in payload:
                payload[key] = recovery[key]
    return {"data": payload}


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
    candidate_provider: CandidateProvider | None = None
    model_decision_required: bool = False


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
        candidate_provider: CandidateProvider | None = None,
    ) -> None:
        self.adapter = adapter
        self.robot_ip = robot_ip
        self.run_id = run_id
        self.queue = queue
        self.state = state
        self.config = config
        self.candidate_provider = candidate_provider or config.candidate_provider

    def _resolve_action(
        self,
        *,
        recovery: Mapping[str, Any],
        branch: str,
    ) -> tuple[CandidateAction | None, GatekeeperDecision | None, str | None]:
        human_confirmed = self.config.auto_execute

        if self.config.model_decision_required:
            if self.candidate_provider is None:
                return None, None, None
            try:
                llm_action = suggest_action(self.state, self.candidate_provider)
            except ValueError:
                return None, None, None
            if llm_action is None:
                return None, None, None
            return (
                llm_action,
                evaluate_runtime_action(llm_action, self.state),
                "llm_planner",
            )

        if _deterministic_candidate_viable(
            recovery=recovery,
            branch=branch,
            auto_execute=self.config.auto_execute,
        ):
            deterministic_action = _deterministic_action(
                branch=branch,
                human_confirmed=human_confirmed,
            )
            deterministic_decision = evaluate_runtime_action(deterministic_action, self.state)
            if deterministic_decision.approved:
                return deterministic_action, deterministic_decision, "deterministic"

        if self.candidate_provider is None:
            if branch and _deterministic_candidate_viable(
                recovery=recovery,
                branch=branch,
                auto_execute=False,
            ):
                deterministic_action = _deterministic_action(
                    branch=branch,
                    human_confirmed=human_confirmed,
                )
                return (
                    deterministic_action,
                    evaluate_runtime_action(deterministic_action, self.state),
                    "deterministic",
                )
            return None, None, None

        try:
            llm_action = suggest_action(self.state, self.candidate_provider)
        except ValueError:
            return None, None, None
        if llm_action is None:
            return None, None, None
        return llm_action, evaluate_runtime_action(llm_action, self.state), "llm_planner"

    def step(self) -> dict[str, Any]:
        snapshot = self.adapter.recovery_snapshot(robot_ip=self.robot_ip, run_id=self.run_id)
        errors = snapshot_errors(snapshot)
        if errors:
            return {"status": "mcp_error", "snapshot": snapshot, "errors": errors}

        autonomy_mode = str(self.state.expected.get("autonomy_mode", "auto"))
        live_state = self.adapter.state_from_snapshot(
            robot_ip=self.robot_ip,
            run_id=self.run_id,
            snapshot=snapshot,
            autonomy_mode=autonomy_mode,
        )
        self.state = _merge_runtime_state(self.state, live_state)
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
        if parsed_error or branch or memory_hits:
            self.state = _inject_error_observation(
                self.state,
                parsed_error=parsed_error,
                memory_hits=memory_hits,
                branch=branch,
                recovery=recovery if branch else None,
            )

        action, decision, action_source = self._resolve_action(recovery=recovery, branch=branch)
        if action is None or decision is None:
            return {
                "status": "no_action",
                "snapshot": snapshot,
                "parsed_error": parsed_error,
                "memory_hits": memory_hits,
                "recovery": recovery if branch else None,
            }

        branch = _action_branch(action) or branch
        common_payload = {
            "decision": decision.to_dict(),
            "parsed_error": parsed_error,
            "recovery": recovery,
            "memory_hits": memory_hits,
            "action": action.to_dict(),
            "action_source": action_source,
        }

        if not decision.approved:
            return {
                "status": "escalated" if decision.escalated else "blocked",
                **common_payload,
            }

        if action.action_type != "execute_recovery_branch":
            return {
                "status": "awaiting_confirmation",
                **common_payload,
            }

        if self.config.auto_execute and recovery.get("auto_executable") is False and action_source == "deterministic":
            return {
                "status": "escalated",
                "reasons": ("recovery branch is not auto_executable",),
                **common_payload,
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
                **common_payload,
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
                    "memory_outcomes": memory_outcomes,
                    **common_payload,
                }

        if not self.config.auto_execute:
            return {
                "status": "awaiting_confirmation",
                "memory_outcomes": memory_outcomes,
                "preview": {
                    "branch": branch,
                    "failed_command_id": failed_command_id,
                    "error_leaf": parsed_error.get("error_leaf"),
                    "auto_executable": recovery.get("auto_executable"),
                },
                **common_payload,
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

        execution_suggestion = _execution_suggestion(
            mcp_suggestion=suggestion,
            recovery=recovery,
            action=action,
        )
        result = self.adapter.execute_suggested_recovery(
            robot_ip=self.robot_ip,
            run_id=self.run_id,
            suggestion=execution_suggestion,
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
            "execution": result,
            "memory_outcomes": memory_outcomes,
            **common_payload,
        }
