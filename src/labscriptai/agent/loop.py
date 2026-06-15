"""Turn-based unified agent loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from labscriptai.agent.registry import ToolRegistry
from labscriptai.agent.state import AgentState
from labscriptai.agent.tools import ToolCall, ToolResult
from labscriptai.runtime.trace import TraceEvent


@dataclass(frozen=True)
class LoopResult:
    final_state: AgentState
    completed: bool


class LabscriptAgentLoop:
    def __init__(
        self,
        *,
        client: Any,
        registry: ToolRegistry,
        max_steps: int = 12,
        initial_messages: list[dict[str, Any]] | None = None,
    ) -> None:
        self.client = client
        self.registry = registry
        self.max_steps = max_steps
        self.initial_messages = initial_messages
        self.messages: list[dict[str, Any]] = []
        self.last_tool_results: list[ToolResult] = []
        self.final_response: dict[str, Any] | None = None

    def run(self, state: AgentState) -> LoopResult:
        completed = False
        state.trace.append(
            TraceEvent(run_id=state.run_id, event_type="state_update", actor="system", payload=state.to_dict())
        )
        self.messages = list(self.initial_messages) if self.initial_messages is not None else _initial_messages(state)
        for _ in range(self.max_steps):
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
                    break
            state.trace.append(
                TraceEvent(run_id=state.run_id, event_type="state_update", actor="system", payload=state.to_dict())
            )
            if state.phase in {"aborted", "failed"}:
                break
            if state.mode == "run" and state.phase in {"paused", "completed"}:
                break
        if state.mode == "author":
            completed = state.package_ready and _required_files_exist(state)
        state.trace.append(
            TraceEvent(
                run_id=state.run_id,
                event_type="summary",
                actor="system",
                payload={"completed": completed, **state.to_dict()},
            )
        )
        return LoopResult(final_state=state, completed=completed)

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
