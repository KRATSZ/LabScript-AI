"""Turn-based unified agent loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from labscriptai.agent.registry import ToolRegistry
from labscriptai.agent.state import AgentState
from labscriptai.agent.suspend import (
    SuspendStore,
    deserialize_agent_state,
    deserialize_tool_call,
    new_suspend_id,
    serialize_agent_state,
    serialize_tool_call,
    SuspendedLoopSnapshot,
)
from labscriptai.agent.tools import ToolCall, ToolResult
from labscriptai.runtime.trace import TraceEvent


@dataclass(frozen=True)
class LoopResult:
    final_state: AgentState
    completed: bool
    suspended: bool = False
    suspend_id: str | None = None


class LabscriptAgentLoop:
    def __init__(
        self,
        *,
        client: Any,
        registry: ToolRegistry,
        max_steps: int = 12,
        initial_messages: list[dict[str, Any]] | None = None,
        suspend_store: SuspendStore | None = None,
        suspend_dir: Path | str | None = None,
    ) -> None:
        self.client = client
        self.registry = registry
        self.max_steps = max_steps
        self.initial_messages = initial_messages
        self.suspend_store = suspend_store or SuspendStore()
        self.suspend_dir = Path(suspend_dir) if suspend_dir is not None else None
        self.messages: list[dict[str, Any]] = []
        self.last_tool_results: list[ToolResult] = []
        self.final_response: dict[str, Any] | None = None

    def run(self, state: AgentState) -> LoopResult:
        self.messages = list(self.initial_messages) if self.initial_messages is not None else _initial_messages(state)
        return self._execute_loop(state, steps_remaining=self.max_steps)

    def resume_loop(
        self,
        suspend_id: str,
        payload: Mapping[str, Any],
    ) -> LoopResult:
        if not bool(payload.get("human_confirmed")):
            raise ValueError("resume_loop requires human_confirmed=true in payload")
        snapshot = self.suspend_store.pop(suspend_id, persist_dir=self.suspend_dir)
        state = deserialize_agent_state(snapshot.state_payload)
        self.messages = list(snapshot.messages)
        pending_call = _apply_human_confirmation(
            deserialize_tool_call(snapshot.pending_call),
            payload,
        )
        self._append_human_confirmation_message(suspend_id, payload)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="observation",
                actor="human",
                payload={
                    "suspend_id": suspend_id,
                    "human_confirmed": True,
                    **{key: value for key, value in payload.items() if key != "human_confirmed"},
                },
                state_hash=state.stable_hash(),
            )
        )
        result = self.registry.call_with_gating(pending_call, state)
        self.last_tool_results.append(result)
        state = state.apply(result.state_patch).with_counters(tool_calls=1)
        self._append_tool_message(pending_call, result)
        if result.decision and result.decision.blocked:
            state = state.with_phase("paused")
        elif result.decision and result.decision.escalated:
            return self._suspend(state, pending_call, steps_remaining=snapshot.steps_remaining)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="state_update",
                actor="system",
                payload=state.to_dict(),
            )
        )
        if state.phase in {"aborted", "failed"}:
            return self._finalize_loop(state, completed=False, suspended=False)
        if state.mode == "run" and state.phase in {"paused", "completed"}:
            return self._finalize_loop(state, completed=state.phase == "completed", suspended=False)
        return self._execute_loop(state, steps_remaining=snapshot.steps_remaining)

    def _execute_loop(self, state: AgentState, *, steps_remaining: int) -> LoopResult:
        completed = False
        state.trace.append(
            TraceEvent(run_id=state.run_id, event_type="state_update", actor="system", payload=state.to_dict())
        )
        for step_index in range(steps_remaining):
            response = self.client.complete(self.messages, self.registry.list_specs(mode=state.mode))
            state = state.with_counters(
                steps=1,
                input_tokens=int(getattr(self.client, "input_tokens", 0)) - state.counters.input_tokens,
                output_tokens=int(getattr(self.client, "output_tokens", 0)) - state.counters.output_tokens,
                total_tokens=int(getattr(self.client, "total_tokens", 0)) - state.counters.total_tokens,
            )
            assistant_message = response.get("_assistant_message")
            self.messages.append(
                assistant_message
                if isinstance(assistant_message, dict)
                else {"role": "assistant", "content": json.dumps(response, ensure_ascii=False)}
            )
            if isinstance(response.get("final"), dict):
                self.final_response = response["final"]
                state, completed = self._finalize(state, response["final"])
                if completed or state.mode == "run":
                    break
                self.messages.append(_package_incomplete_message(state))
                continue
            calls = response.get("tool_calls") or []
            if not isinstance(calls, list) or not calls:
                break
            for raw in calls:
                if not isinstance(raw, dict):
                    continue
                call = ToolCall.from_model(raw)
                result = self.registry.call_with_gating(call, state)
                self.last_tool_results.append(result)
                state = state.apply(result.state_patch).with_counters(tool_calls=1)
                self._append_tool_message(call, result)
                if state.mode == "run" and result.decision and result.decision.blocked:
                    state = state.with_phase("paused")
                    break
                if state.mode == "run" and result.decision and result.decision.escalated:
                    state = state.with_phase("recovering")
                    remaining = steps_remaining - step_index - 1
                    return self._suspend(state, call, steps_remaining=remaining)
            state.trace.append(
                TraceEvent(run_id=state.run_id, event_type="state_update", actor="system", payload=state.to_dict())
            )
            if state.phase in {"aborted", "failed"}:
                break
            if state.mode == "run" and state.phase in {"paused", "completed"}:
                break
        if state.mode == "author":
            completed = state.package_ready and _required_files_exist(state)
        return self._finalize_loop(state, completed=completed, suspended=False)

    def _suspend(self, state: AgentState, call: ToolCall, *, steps_remaining: int) -> LoopResult:
        suspend_id = new_suspend_id(run_id=state.run_id)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="escalation",
                actor="system",
                payload={
                    "reason": "human confirmation required",
                    "tool_name": call.name,
                    "tool_call": call.to_dict(),
                    "suspend_id": suspend_id,
                },
                state_hash=state.stable_hash(),
            )
        )
        snapshot = SuspendedLoopSnapshot(
            suspend_id=suspend_id,
            state_payload=serialize_agent_state(state),
            messages=list(self.messages),
            pending_call=serialize_tool_call(call),
            steps_remaining=steps_remaining,
            initial_messages=list(self.initial_messages) if self.initial_messages is not None else None,
        )
        persist_dir = self.suspend_dir
        if persist_dir is None:
            persist_dir = state.trace_path.parent / "suspended"
        self.suspend_store.save(snapshot, persist_dir=persist_dir)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="summary",
                actor="system",
                payload={"completed": False, "suspended": True, "suspend_id": suspend_id, **state.to_dict()},
            )
        )
        return LoopResult(final_state=state, completed=False, suspended=True, suspend_id=suspend_id)

    def _finalize_loop(self, state: AgentState, *, completed: bool, suspended: bool) -> LoopResult:
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="summary",
                actor="system",
                payload={"completed": completed, "suspended": suspended, **state.to_dict()},
            )
        )
        return LoopResult(final_state=state, completed=completed, suspended=suspended)

    def _append_human_confirmation_message(self, suspend_id: str, payload: Mapping[str, Any]) -> None:
        self.messages.append(
            {
                "role": "system",
                "content": json.dumps(
                    {
                        "human_confirmation": {
                            "suspend_id": suspend_id,
                            "human_confirmed": True,
                            **{key: value for key, value in payload.items()},
                        }
                    },
                    ensure_ascii=False,
                    default=str,
                ),
            }
        )

    def _finalize(self, state: AgentState, final: dict[str, Any]) -> tuple[AgentState, bool]:
        if state.mode == "author":
            if bool(final.get("package_ready")) and _required_files_exist(state):
                return state.with_package_ready(True), True
            return state, False
        if final.get("completed") or state.phase == "completed":
            return state.with_phase("completed"), True
        return state, False

    def _append_tool_message(self, call: ToolCall, result: ToolResult) -> None:
        if call.call_id:
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "content": json.dumps(result.to_dict(), ensure_ascii=False),
                }
            )
        else:
            self.messages.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {"tool_result": {"name": call.name, "result": result.to_dict()}},
                        ensure_ascii=False,
                        default=str,
                    ),
                }
            )


def resume_loop(
    loop: LabscriptAgentLoop,
    suspend_id: str,
    payload: Mapping[str, Any],
) -> LoopResult:
    """Resume a suspended loop after explicit human confirmation."""
    return loop.resume_loop(suspend_id, payload)


def _apply_human_confirmation(call: ToolCall, payload: Mapping[str, Any]) -> ToolCall:
    arguments = dict(call.arguments)
    arguments["human_confirmed"] = True
    for key, value in payload.items():
        if key == "human_confirmed":
            continue
        arguments[key] = value
    return ToolCall(
        name=call.name,
        arguments=arguments,
        reason=call.reason,
        proposed_by=call.proposed_by,
        call_id=call.call_id,
    )


def _initial_messages(state: AgentState) -> list[dict[str, Any]]:
    required_files = list(state.task_spec.required_files)
    return [
        {
            "role": "system",
            "content": (
                "You are LabscriptAI. Use tool_calls only until ready. "
                f"Author mode must produce these files: {', '.join(required_files)}."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task_id": state.task_spec.task_id,
                    "difficulty": state.task_spec.difficulty,
                    "prompt": state.task_spec.prompt,
                    "required_package_files": required_files,
                },
                ensure_ascii=False,
            ),
        },
    ]


def _package_incomplete_message(state: AgentState) -> dict[str, str]:
    missing = [name for name in state.task_spec.required_files if not (state.package.dir / name).exists()]
    return {
        "role": "user",
        "content": json.dumps(
            {
                "package_incomplete": {
                    "missing_required_files": missing,
                    "instruction": "Write the missing files before returning final.",
                }
            },
            ensure_ascii=False,
        ),
    }


def _required_files_exist(state: AgentState) -> bool:
    return all((state.package.dir / name).exists() for name in state.task_spec.required_files)
