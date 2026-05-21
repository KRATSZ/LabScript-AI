"""Minimal offline LabscriptAI runtime loop."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .actions import CandidateAction
from .adapters.simulator import simulate_protocol_package
from .continuation import validate_continuation_patch
from .gatekeeper import GatekeeperDecision, evaluate_action
from .patch_log import PatchLogEntry, PatchLogWriter
from .state import RuntimeState
from .trace import TraceEvent, TraceWriter

CandidateProvider = Callable[[RuntimeState], Mapping[str, Any] | CandidateAction | None]


@dataclass(frozen=True)
class LoopResult:
    final_state: RuntimeState
    decisions: tuple[GatekeeperDecision, ...]
    completed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "final_state": self.final_state.to_dict(),
            "decisions": [decision.to_dict() for decision in self.decisions],
        }


class ScriptedCandidateProvider:
    """Deterministic provider used for offline tests and demos."""

    def __init__(self, actions: Iterable[Mapping[str, Any] | CandidateAction]) -> None:
        self._actions: Iterator[Mapping[str, Any] | CandidateAction] = iter(actions)

    def __call__(self, state: RuntimeState) -> Mapping[str, Any] | CandidateAction | None:
        del state
        return next(self._actions, None)


def _coerce_action(payload: Mapping[str, Any] | CandidateAction) -> CandidateAction:
    if isinstance(payload, CandidateAction):
        return payload
    return CandidateAction.from_mapping(payload)


def run_offline_loop(
    *,
    initial_state: RuntimeState,
    package_dir: Path | str,
    trace_path: Path | str,
    candidate_provider: CandidateProvider,
    max_steps: int = 8,
    simulation_pass: bool = False,
    patch_log_path: Path | str | None = None,
) -> LoopResult:
    """Run the first offline loop: package validation, candidate action, gate, trace."""

    state = initial_state
    writer = TraceWriter(trace_path)
    patch_writer = PatchLogWriter(patch_log_path) if patch_log_path is not None else None
    decisions: list[GatekeeperDecision] = []

    validation_payload = simulate_protocol_package(package_dir, simulation_pass=simulation_pass)
    validation_ok = bool(validation_payload.get("ok"))
    writer.append(
        TraceEvent.for_state(
            state,
            event_type="tool_result",
            actor="tool",
            payload={"tool": "package_validator", "result": validation_payload},
        )
    )
    if validation_ok:
        state = state.with_phase("ready")
    else:
        state = state.with_phase("paused")
    writer.append(
        TraceEvent.for_state(
            state,
            event_type="state_update",
            actor="system",
            payload={"phase": state.phase, "source": "package_validator"},
        )
    )

    for _ in range(max_steps):
        raw_action = candidate_provider(state)
        if raw_action is None:
            break

        try:
            action = _coerce_action(raw_action)
        except ValueError as exc:
            writer.append(
                TraceEvent.for_state(
                    state,
                    event_type="gatekeeper_decision",
                    actor="gatekeeper",
                    payload={"status": "blocked", "reason": str(exc)},
                )
            )
            continue

        writer.append(
            TraceEvent.for_state(
                state,
                event_type="candidate_action",
                actor="model",
                payload=action.to_dict(),
            )
        )
        decision = evaluate_action(action, state)
        decisions.append(decision)
        writer.append(
            TraceEvent.for_state(
                state,
                event_type="gatekeeper_decision",
                actor="gatekeeper",
                payload=decision.to_dict(),
                )
            )

        if action.action_type in {
            "propose_continuation_patch",
            "validate_continuation_patch",
            "execute_recovery_branch",
        }:
            patch = action.parameters.get("patch")
            validation_payload = None
            if isinstance(patch, Mapping):
                validation_payload = validate_continuation_patch(
                    patch,
                    state,
                    require_human_confirmation=action.action_type == "execute_recovery_branch",
                ).to_dict()
                writer.append(
                    TraceEvent.for_state(
                        state,
                        event_type="recovery",
                        actor="gatekeeper",
                        payload={
                            "action_type": action.action_type,
                            "patch_validation": validation_payload,
                        },
                    )
                )
            if patch_writer is not None and isinstance(patch, Mapping):
                patch_writer.append(
                    PatchLogEntry(
                        run_id=state.run_id,
                        old_state_hash=state.stable_hash(),
                        patch=patch,
                        reason=action.reason,
                        gatekeeper_decision=decision.to_dict(),
                        human_confirmed=bool(action.parameters.get("human_confirmed")),
                        result={"dry_run": True, "validation": validation_payload},
                    )
                )

        if decision.blocked:
            state = state.with_phase("paused")
            writer.append(
                TraceEvent.for_state(
                    state,
                    event_type="escalation",
                    actor="system",
                    payload={"reason": "candidate action blocked", "action_type": action.action_type},
                )
            )
            break
        if decision.escalated:
            state = state.with_phase("recovering")
            writer.append(
                TraceEvent.for_state(
                    state,
                    event_type="escalation",
                    actor="system",
                    payload={"reason": "human confirmation required", "action_type": action.action_type},
                )
            )
            break

        if action.action_type in {"pause_run", "request_human_confirmation"}:
            state = state.with_phase("paused")
        elif action.action_type == "abort_run":
            state = state.with_phase("aborted")
        elif action.action_type == "resume_run":
            state = state.with_phase("running")

        writer.append(
            TraceEvent.for_state(
                state,
                event_type="tool_call",
                actor="tool",
                payload={"action_type": action.action_type, "dry_run": True},
            )
        )

    completed = validation_ok and bool(decisions) and all(
        decision.approved for decision in decisions
    )
    writer.append(
        TraceEvent.for_state(
            state,
            event_type="summary",
            actor="system",
            payload={"completed": completed, "decision_count": len(decisions)},
        )
    )
    return LoopResult(final_state=state, decisions=tuple(decisions), completed=completed)
